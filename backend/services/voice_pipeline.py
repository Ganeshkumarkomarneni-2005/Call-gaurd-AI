"""
Voice Pipeline Orchestrator.

Ties together the Telephony, STT, LLM, TTS, and Analysis components into
a single cohesive call-processing pipeline:

    Audio Stream -> STT -> ConversationManager -> LLM -> TTS -> Audio Out
                                   |
                            AnalysisPipeline

Each active call runs its own pipeline instance. Instances are lightweight
and should be created per-call, not shared.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog

from backend.services.conversation_manager import ConversationManager, ConversationTurn
from backend.services.telephony.base import TelephonyCallInfo

if TYPE_CHECKING:
    from backend.services.telephony.base import BaseTelephonyProvider
    from backend.services.stt.base import BaseSTTProvider
    from backend.services.tts.base import BaseTTSProvider
    from backend.services.llm.base import BaseLLMProvider

logger = structlog.get_logger(__name__)

# ------------------------------------------------------------------
# System prompt template for the screening agent
# ------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are CallGuard AI, an intelligent call-screening assistant protecting the user from \
spam, fraud, and scam calls. Your job is to:
1. Politely answer calls on behalf of the user.
2. Identify the caller and their purpose.
3. Detect signs of fraud (payment requests, OTP demands, high-pressure tactics).
4. Decide whether to transfer the call to the user, continue screening, or end the call.

Speak naturally and professionally. Keep responses concise (1-3 sentences).
"""

# Intent signals that warrant ending the call immediately
_DANGER_KEYWORDS = frozenset(
    ["otp", "pin", "password", "pay now", "rupees", "upi", "wire transfer", "urgent fee"]
)


class VoicePipeline:
    """
    Orchestrates the voice AI pipeline for a single active call.

    Audio Stream -> STT -> ConversationManager -> LLM -> TTS -> Audio Out

    The pipeline is stateless beyond what is stored in the
    :class:`ConversationManager`. Create one instance per call.
    """

    def __init__(
        self,
        telephony: "BaseTelephonyProvider",
        stt: "BaseSTTProvider",
        tts: "BaseTTSProvider",
        llm: "BaseLLMProvider",
        analysis_pipeline: Any | None = None,
        conversation_manager: ConversationManager | None = None,
    ) -> None:
        """
        Args:
            telephony: Telephony provider instance (handles audio I/O).
            stt: Speech-to-Text provider.
            tts: Text-to-Speech provider.
            llm: Large Language Model provider.
            analysis_pipeline: Optional analysis pipeline for real-time fraud
                detection. If None, analysis is skipped during the call.
            conversation_manager: Shared conversation state manager. A new one
                is created if not provided.
        """
        self.telephony = telephony
        self.stt = stt
        self.tts = tts
        self.llm = llm
        self.analysis = analysis_pipeline
        self.conversation = conversation_manager or ConversationManager()
        self.logger = structlog.get_logger(__name__)
        self._audio_tasks: dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Call lifecycle
    # ------------------------------------------------------------------

    async def start_call(self, call_id: str, call_info: TelephonyCallInfo) -> None:
        """Begin processing a call.

        Answers the call, starts the conversation, plays the opening greeting,
        and launches the background audio-streaming task.

        Args:
            call_id: Unique identifier of the call.
            call_info: Metadata snapshot for the incoming call.
        """
        self.logger.info("Starting call pipeline", call_id=call_id)

        # Initialise conversation state
        self.conversation.start_conversation(call_id)
        self.conversation.set_state(call_id, "call_info", {
            "caller_number": call_info.caller_number,
            "virtual_number": call_info.virtual_number,
            "provider": call_info.provider,
            "started_at": call_info.started_at.isoformat(),
        })
        self.conversation.set_state(call_id, "risk_score", 0.0)
        self.conversation.set_state(call_id, "flags", [])

        # Answer the call
        answered = await self.telephony.answer_call(call_id)
        if not answered:
            self.logger.error("Failed to answer call", call_id=call_id)
            return

        # Send opening greeting
        greeting = await self.llm.generate(
            prompt="Call just started. Caller has not spoken yet.",
            system=_SYSTEM_PROMPT,
        )
        await self._speak(call_id, greeting, speaker_label="agent")

        # Launch background audio processing task
        task = asyncio.create_task(
            self._audio_processing_loop(call_id),
            name=f"audio-loop-{call_id}",
        )
        self._audio_tasks[call_id] = task
        self.logger.info("Call pipeline started", call_id=call_id)

    async def process_turn(self, call_id: str, caller_text: str) -> str:
        """Process one conversation turn.

        Runs the full pipeline for a single caller utterance:
        1. Record caller text in conversation history.
        2. Run incremental analysis (if analysis_pipeline present).
        3. Check for immediate danger signals.
        4. Generate agent response via LLM.
        5. Synthesise response audio and send to caller.
        6. Return the agent response text.

        Args:
            call_id: Unique identifier of the call.
            caller_text: Transcribed caller utterance.

        Returns:
            Agent response text string.
        """
        self.logger.info(
            "Processing turn",
            call_id=call_id,
            caller_text_preview=caller_text[:80],
        )

        # 1. Record caller text
        self.conversation.add_turn(call_id, speaker="caller", text=caller_text)

        # 2. Run incremental analysis
        if self.analysis is not None:
            try:
                analysis_result = await self.analysis.analyze_incremental(
                    call_id=call_id,
                    transcript=self.conversation.get_conversation_as_text(call_id),
                )
                if isinstance(analysis_result, dict):
                    risk = analysis_result.get("risk_score", 0.0)
                    self.conversation.set_state(call_id, "risk_score", risk)
                    flags = analysis_result.get("flags", [])
                    existing = self.conversation.get_state(call_id, "flags", [])
                    self.conversation.set_state(call_id, "flags", existing + flags)
            except Exception as exc:
                self.logger.warning(
                    "Incremental analysis failed", call_id=call_id, error=str(exc)
                )

        # 3. Check for immediate danger signals
        lower_text = caller_text.lower()
        danger_detected = any(kw in lower_text for kw in _DANGER_KEYWORDS)
        if danger_detected:
            self.logger.warning(
                "Danger keyword detected, flagging call",
                call_id=call_id,
                text=caller_text,
            )
            flags = self.conversation.get_state(call_id, "flags", [])
            flags.append("danger_keyword")
            self.conversation.set_state(call_id, "flags", flags)

        # 4. Determine agent response
        history_text = self.conversation.get_conversation_as_text(call_id)
        response_text = await self.llm.generate(
            prompt=history_text,
            system=_SYSTEM_PROMPT,
        )

        # 5. Synthesise and send audio
        await self._speak(call_id, response_text, speaker_label="agent")

        return response_text

    async def finalize_call(self, call_id: str) -> dict[str, Any]:
        """Run final analysis and return complete call results.

        Cancels the audio loop, ends the conversation, and runs the full
        analysis pipeline to produce the final call report.

        Args:
            call_id: Unique identifier of the call.

        Returns:
            Dictionary containing:
            - ``transcript``: List of turn dicts.
            - ``analysis``: Final analysis report dict (if available).
            - ``risk_score``: Running risk score at call end.
            - ``flags``: Accumulated flag list.
            - ``state``: Full call state snapshot.
        """
        self.logger.info("Finalising call", call_id=call_id)

        # Cancel audio loop if still running
        task = self._audio_tasks.pop(call_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # End the conversation
        history: list[ConversationTurn] = self.conversation.end_conversation(call_id)
        state = self.conversation.get_all_state(call_id)

        transcript = [
            {
                "speaker": t.speaker,
                "text": t.text,
                "timestamp": t.timestamp.isoformat(),
                "metadata": t.metadata,
            }
            for t in history
        ]

        # Run final analysis pipeline
        analysis_report: dict[str, Any] = {}
        if self.analysis is not None:
            try:
                full_transcript = "\n".join(
                    f"{'Agent' if t['speaker'] == 'agent' else 'Caller'}: {t['text']}"
                    for t in transcript
                )
                analysis_report = await self.analysis.analyze_full(
                    call_id=call_id,
                    transcript=full_transcript,
                )
            except Exception as exc:
                self.logger.warning(
                    "Final analysis failed", call_id=call_id, error=str(exc)
                )

        result = {
            "call_id": call_id,
            "transcript": transcript,
            "analysis": analysis_report,
            "risk_score": state.get("risk_score", 0.0),
            "flags": state.get("flags", []),
            "state": state,
        }
        self.logger.info(
            "Call finalised",
            call_id=call_id,
            turns=len(transcript),
            risk_score=result["risk_score"],
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _speak(self, call_id: str, text: str, speaker_label: str = "agent") -> None:
        """Synthesise *text* and send the audio to the caller.

        Also records the turn in the conversation history.

        Args:
            call_id: Unique identifier of the call.
            text: Text to speak.
            speaker_label: Speaker label for conversation history.
        """
        # Record in conversation history
        if speaker_label == "agent":
            self.conversation.add_turn(call_id, speaker="agent", text=text)

        # Synthesise audio
        try:
            audio_bytes = await self.tts.synthesize(text)
        except Exception as exc:
            self.logger.error(
                "TTS synthesis failed, falling back to play_tts",
                call_id=call_id,
                error=str(exc),
            )
            await self.telephony.play_tts(call_id, text)
            return

        # Send to caller
        success = await self.telephony.send_audio(call_id, audio_bytes)
        if not success:
            # Fallback: ask provider to handle TTS natively
            await self.telephony.play_tts(call_id, text)

    async def _audio_processing_loop(self, call_id: str) -> None:
        """Background task: consume audio stream and process each utterance.

        Reads chunks from the telephony audio stream, feeds them to STT, and
        calls :py:meth:`process_turn` for each transcribed utterance.

        Args:
            call_id: Unique identifier of the call.
        """
        self.logger.info("Audio processing loop started", call_id=call_id)
        accumulated: list[bytes] = []
        silence_streak = 0
        max_silence_chunks = 50  # ~1 s of silence before flushing

        try:
            async for chunk in await self.telephony.stream_audio(call_id):
                accumulated.append(chunk)
                # Detect silence (all-zero chunk)
                if chunk == bytes(len(chunk)):
                    silence_streak += 1
                else:
                    silence_streak = 0

                # Flush on silence boundary (~1 s of accumulated audio)
                if silence_streak >= max_silence_chunks and len(accumulated) > max_silence_chunks:
                    audio_data = b"".join(accumulated)
                    accumulated = []
                    silence_streak = 0

                    transcript = await self.stt.transcribe_audio(audio_data)
                    if transcript.strip():
                        await self.process_turn(call_id, transcript)

        except asyncio.CancelledError:
            self.logger.info("Audio processing loop cancelled", call_id=call_id)
        except Exception as exc:
            self.logger.error(
                "Audio processing loop error",
                call_id=call_id,
                error=str(exc),
                exc_info=True,
            )
        finally:
            self.logger.info("Audio processing loop ended", call_id=call_id)
