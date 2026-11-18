import json
import os
from concurrent import futures
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import grpc
import httpx
from llm import llm_service


class CustomerSupportFallbackTests(unittest.TestCase):
    def test_provider_uses_llm_model_compatibility_setting(self):
        with patch.dict(os.environ, {"LLM_MODEL": "configured-model"}, clear=True):
            status = llm_service.provider_status()

        self.assertEqual(status["model"], "configured-model")

    def test_seat_answer_does_not_invent_live_availability(self):
        response = llm_service.answer_question("Which seats are available?")

        self.assertIn("checked live", response)
        self.assertNotIn("A1", response)

    def test_cancellation_faq_has_a_safe_fallback(self):
        response = llm_service.answer_question("How do I cancel my booking?")

        self.assertIn("Only confirmed bookings", response)
        self.assertIn("My Bookings", response)

    def test_provider_failure_uses_deterministic_fallback(self):
        request = llm_service.llm_pb2.Question(
            text="Which seats are available?",
            context=json.dumps({}),
        )
        with patch.object(llm_service, "generate_llm_response", side_effect=RuntimeError("provider unavailable")):
            response = llm_service.LLMService().AskQuestion(request, None)

        self.assertTrue(response.success)
        self.assertEqual(response.status, "fallback")
        self.assertIn("checked live", response.response)

    def test_connection_error_retries_and_sends_bounded_conversation_history(self):
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Actual model response."))])
        completion = Mock(side_effect=[
            llm_service.APIConnectionError(
                message="connection failed",
                request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
            ),
            response,
        ])
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
        context = {
            "events": [{"title": "Jazz Night"}],
            "conversation": [
                {"role": "user", "content": "Can I book two tickets?"},
                {"role": "assistant", "content": "Choose an event and seats."},
            ],
        }

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "test-model"}):
            with patch.object(llm_service, "Groq", return_value=client) as groq_client:
                with patch.object(llm_service.time, "sleep") as sleep:
                    answer = llm_service.generate_llm_response("How do I pay?", context)

        self.assertEqual(answer, "Actual model response.")
        groq_client.assert_called_once_with(api_key="test-key", timeout=8, max_retries=0)
        self.assertEqual(completion.call_count, 2)
        self.assertEqual(sleep.call_args.args, (0.25,))
        messages = completion.call_args.kwargs["messages"]
        self.assertEqual([item["role"] for item in messages], ["system", "user", "assistant", "user"])
        self.assertIn('"title": "Jazz Night"', messages[-1]["content"])
        self.assertNotIn('"conversation"', messages[-1]["content"])

    def test_non_retryable_provider_error_is_not_retried(self):
        completion = Mock(side_effect=ValueError("invalid request"))
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch.object(llm_service, "Groq", return_value=client):
                with patch.object(llm_service.time, "sleep") as sleep:
                    with self.assertRaisesRegex(ValueError, "invalid request"):
                        llm_service.generate_llm_response("Question")
        self.assertEqual(completion.call_count, 1)
        sleep.assert_not_called()

    def test_retry_attempt_timeouts_fit_inside_grpc_deadline(self):
        with patch.dict(os.environ, {"LLM_GRPC_TIMEOUT_MS": "5000"}):
            timeout_ms = llm_service._bounded_provider_timeout(8000, 3, 250)
        self.assertEqual(timeout_ms, 562)

    def test_provider_check_uses_configured_model_without_exposing_credentials(self):
        model = SimpleNamespace(id="test-model")
        retrieve = Mock(return_value=model)
        client = SimpleNamespace(models=SimpleNamespace(retrieve=retrieve))
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "test-model"}):
            with patch.object(llm_service, "Groq", return_value=client) as groq_client:
                self.assertIs(llm_service.check_provider(), model)
        groq_client.assert_called_once_with(api_key="test-key", timeout=8, max_retries=0)
        retrieve.assert_called_once_with("test-model")

    def test_grpc_service_handles_twenty_concurrent_requests(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=12))
        llm_service.llm_pb2_grpc.add_LLMServiceServicer_to_server(llm_service.LLMService(), server)
        port = server.add_insecure_port("127.0.0.1:0")
        server.start()
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        stub = llm_service.llm_pb2_grpc.LLMServiceStub(channel)

        def fake_generate(question, _context):
            return f"Answer: {question}"

        try:
            with patch.object(llm_service, "generate_llm_response", side_effect=fake_generate):
                with futures.ThreadPoolExecutor(max_workers=20) as callers:
                    responses = list(callers.map(
                        lambda index: stub.AskQuestion(
                            llm_service.llm_pb2.Question(text=f"Question {index}"),
                            timeout=5,
                        ),
                        range(20),
                    ))
            self.assertEqual(len(responses), 20)
            self.assertTrue(all(response.success and response.status == "ok" for response in responses))
            self.assertEqual(
                {response.response for response in responses},
                {f"Answer: Question {index}" for index in range(20)},
            )
        finally:
            channel.close()
            server.stop(grace=0).wait()


if __name__ == "__main__":
    unittest.main()
