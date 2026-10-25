import http.client
import importlib.util
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "ci" / "opencode_agent.py"
FAKE_CLIENT = Path(__file__).resolve().parent / "fake_native_client.py"
SPEC = importlib.util.spec_from_file_location("opencode_agent", MODULE_PATH)
agent = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = agent
SPEC.loader.exec_module(agent)


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=agent._git_env(),
    )


def commit(repo, files, message):
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-qm", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip()


class RepoCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        self.base = commit(
            self.repo,
            {
                "a.txt": "old\n",
                "skills/code-review/SKILL.md": "code review skill\n",
                "skills/security-review/SKILL.md": "security review skill\n",
            },
            "base",
        )
        self.head = commit(self.repo, {"a.txt": "new\n"}, "head")
        self.snap = agent.load_snapshot(str(self.repo), self.base, self.head, self.base)

    def tearDown(self):
        self.tmp.cleanup()


class DecisionTest(unittest.TestCase):
    def test_auto_needs_three_valid_votes_two_auto_and_a_non_raising_second(self):
        votes = [agent.Vote("auto", "a"), agent.Vote("auto", "b"), agent.Vote("manual", "c")]
        self.assertEqual(agent.decide(votes, agent.Second(False, "fine")).label, "auto")

    def test_failed_voter_is_manual_even_with_two_auto(self):
        votes = [agent.Vote("auto", "a"), agent.Vote("auto", "b"), None]
        self.assertEqual(agent.decide(votes, agent.Second(False, "fine")).label, "manual")

    def test_majority_manual_stays_manual(self):
        votes = [agent.Vote("auto", "a"), agent.Vote("manual", "b"), agent.Vote("manual", "c")]
        self.assertEqual(agent.decide(votes, agent.Second(False, "fine")).label, "manual")

    def test_missing_second_check_is_manual(self):
        votes = [agent.Vote("auto", "a"), agent.Vote("auto", "b"), agent.Vote("manual", "c")]
        self.assertEqual(agent.decide(votes, None).label, "manual")

    def test_second_check_raises_to_manual(self):
        votes = [agent.Vote("auto", "a"), agent.Vote("auto", "b"), agent.Vote("auto", "c")]
        self.assertEqual(agent.decide(votes, agent.Second(True, "not safe")).label, "manual")

    def test_short_vote_list_is_manual(self):
        self.assertEqual(agent.decide([agent.Vote("auto", "a")], agent.Second(False, "fine")).label, "manual")


class RepositoryBoundaryTest(RepoCase):
    def test_read_file_uses_committed_objects_not_the_worktree(self):
        (self.repo / "a.txt").write_text("dirty\n", encoding="utf-8")
        self.assertIn("new", agent.read_file(self.snap, "head", "a.txt"))
        self.assertNotIn("dirty", agent.read_file(self.snap, "head", "a.txt"))
        self.assertIn("old", agent.read_file(self.snap, "base", "a.txt"))

    def test_read_file_rejects_absolute_and_traversal_paths(self):
        with self.assertRaises(agent.ToolError):
            agent.read_file(self.snap, "head", "../a.txt")
        with self.assertRaises(agent.ToolError):
            agent.read_file(self.snap, "head", "/etc/passwd")
        with self.assertRaises(agent.ToolError):
            agent.read_file(self.snap, "head", "docs/../a.txt")

    def test_read_file_does_not_follow_symlink_blobs(self):
        os.symlink("/etc/passwd", self.repo / "link")
        self.head = commit(self.repo, {}, "link")
        self.snap = agent.load_snapshot(str(self.repo), self.base, self.head, self.base)
        text = agent.read_file(self.snap, "head", "link")
        self.assertEqual(text, "1: /etc/passwd")
        self.assertNotIn("root:", text)

    def test_read_diff_is_limited_to_the_pinned_range(self):
        diff = agent.read_diff(self.snap, "pr")
        self.assertIn("a.txt", diff)
        self.assertIn("-old", diff)
        self.assertIn("+new", diff)


class JsonContentTest(unittest.TestCase):
    def test_fenced_json_is_read(self):
        self.assertEqual(agent._json_content('```json\n{"findings": []}\n```'), {"findings": []})

    def test_prose_is_not_read(self):
        self.assertIsNone(agent._json_content("I found nothing."))


class StreamTest(unittest.TestCase):
    def test_stream_accumulates_tool_arguments_across_chunks(self):
        lines = [
            b'data: {"choices":[{"delta":{"content":"reading"}}]}\n',
            b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call-1","function":{"name":"submit","arguments":"{\\"a\\":"}}]}}]}\n',
            b'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"1}"}}]},"finish_reason":"tool_calls"}]}\n',
            b"data: [DONE]\n",
        ]
        message = agent._message_from_stream(lines)
        self.assertEqual(message["content"], "reading")
        self.assertEqual(message["tool_calls"][0]["function"]["arguments"], '{"a":1}')

    def test_stream_without_finish_raises(self):
        lines = [b'data: {"choices":[{"delta":{"content":"partial"}}]}\n']
        with self.assertRaises(agent.ProviderError):
            agent._message_from_stream(lines)


class Chat(agent.Chat):
    def __init__(self, terminal, arguments):
        self.model = "test"
        self.api_key = "test"
        self.terminal = terminal
        self.arguments = arguments

    def next(self, session, messages, tools, force=None):
        return {
            "content": "",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": self.terminal, "arguments": json.dumps(self.arguments)},
                }
            ],
        }


class MalformedModelOutputTest(RepoCase):
    def test_malformed_vote_is_manual(self):
        with redirect_stderr(io.StringIO()):
            decision = agent.run_risk(self.snap, "", Chat("submit_vote", {"label": "maybe"}))
        self.assertEqual(decision.label, "manual")
        self.assertIn("voter failed", decision.reason)

    def test_malformed_review_finding_raises(self):
        chat = Chat("submit_findings", {"findings": [{"class": "x"}]})
        with self.assertRaises(agent.RunnerError):
            agent.run_review(self.snap, "review this", "", chat)

    def test_a_submit_without_findings_gets_a_second_chance(self):
        chat = ScriptedChat(
            [
                {"content": "", "tool_calls": [terminal_call("submit_findings", {"summary": "nothing"}, "call-1")]},
                {"content": "", "tool_calls": [terminal_call("submit_findings", {"findings": []}, "call-2")]},
            ]
        )
        result = agent._conversation(chat, self.snap, "s", "system", "user", FINDINGS_TOOLS, "submit_findings", 4)
        self.assertEqual(result, {"findings": []})
        retry = chat.seen[1][-1]
        self.assertEqual(retry["role"], "tool")
        self.assertEqual(retry["tool_call_id"], "call-1")
        self.assertIn("submit_findings needs the field findings", retry["content"])

    def test_content_json_with_a_wrong_shape_gets_a_second_chance(self):
        chat = ScriptedChat(
            [
                {"content": '{"findings": "none"}', "tool_calls": []},
                {"content": "", "tool_calls": [terminal_call("submit_findings", {"findings": []})]},
            ]
        )
        result = agent._conversation(chat, self.snap, "s", "system", "user", FINDINGS_TOOLS, "submit_findings", 4)
        self.assertEqual(result, {"findings": []})
        self.assertIn("the field findings of submit_findings must be a JSON array", chat.seen[1][-1]["content"])

    def test_a_model_that_never_fixes_its_shape_still_fails_the_review(self):
        with self.assertRaises(agent.RunnerError):
            agent.run_review(self.snap, "review this", "", Chat("submit_findings", {"summary": "nothing"}))

    def test_a_bad_shape_after_the_turns_run_out_gets_one_more_chance(self):
        reading = {"content": "", "tool_calls": [terminal_call("read_diff", {"scope": "pr"})]}
        chat = ScriptedChat(
            [
                reading,
                reading,
                {"content": '{"summary": "nothing"}', "tool_calls": []},
                {"content": '{"findings": []}', "tool_calls": []},
            ]
        )
        result = agent._conversation(chat, self.snap, "s", "system", "user", FINDINGS_TOOLS, "submit_findings", 2)
        self.assertEqual(result, {"findings": []})
        self.assertIn("submit_findings needs the field findings", chat.seen[3][-1]["content"])

    def test_a_bad_shape_after_the_retry_still_fails_the_review(self):
        reading = {"content": "", "tool_calls": [terminal_call("read_diff", {"scope": "pr"})]}
        summary = {"content": '{"summary": "nothing"}', "tool_calls": []}
        chat = ScriptedChat([reading, reading, summary, summary])
        result = agent._conversation(chat, self.snap, "s", "system", "user", FINDINGS_TOOLS, "submit_findings", 2)
        self.assertEqual(result, {"summary": "nothing"})
        with self.assertRaises(agent.RunnerError):
            agent._parse_findings(result)


class ScriptedChat(agent.Chat):
    def __init__(self, replies):
        self.model = "test"
        self.api_key = "test"
        self.replies = list(replies)
        self.seen = []

    def next(self, session, messages, tools, force=None):
        self.seen.append([dict(message) for message in messages])
        return self.replies.pop(0)


FINDINGS_TOOLS = agent.READ_TOOLS + [
    agent._terminal_tool("submit_findings", "Submit findings.", {"findings": {"type": "array"}}, ["findings"])
]


AUTO = {"submit_vote": {"label": "auto", "reason": "low risk"}, "submit_second": {"raise_to_manual": False, "reason": "fine"}}
MANUAL = {"submit_vote": {"label": "manual", "reason": "risky"}}


def terminal_call(name, arguments, call_id="call-1"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}


class StubStage:
    def __init__(self, replies=None, error=None):
        self.replies = replies or {}
        self.error = error
        self.calls = 0

    def next(self, session, messages, tools, force=None):
        self.calls += 1
        if self.error is not None:
            raise self.error
        terminal = tools[-1]["function"]["name"]
        return {"content": "", "tool_calls": [terminal_call(terminal, self.replies[terminal])]}


class FallbackChainTest(RepoCase):
    def chain(self, *stages):
        self.built = []

        def builder(name, stage):
            def build(root):
                self.built.append(name)
                if isinstance(stage, Exception):
                    raise stage
                return stage

            return name, build

        return agent.FallbackChat(tuple(builder(name, stage) for name, stage in stages))

    def risk(self, *stages):
        with redirect_stderr(io.StringIO()), self.chain(*stages) as chat:
            return agent.run_risk(self.snap, "", chat)

    def test_primary_answers_without_building_fallbacks(self):
        decision = self.risk(("opencode-go", StubStage(AUTO)), ("codex", StubStage(MANUAL)), ("claude", StubStage(MANUAL)))
        self.assertEqual(decision.label, "auto")
        self.assertEqual(self.built, ["opencode-go"])

    def test_primary_outage_moves_the_same_turn_to_codex_and_stays_there(self):
        primary = StubStage(error=agent.AvailabilityError("quota"))
        codex = StubStage(AUTO)
        decision = self.risk(("opencode-go", primary), ("codex", codex), ("claude", StubStage(MANUAL)))
        self.assertEqual(decision.label, "auto")
        self.assertEqual(primary.calls, 1)
        self.assertEqual(codex.calls, 4)
        self.assertEqual(self.built, ["opencode-go", "codex"])

    def test_unavailable_codex_moves_to_claude(self):
        claude = StubStage(AUTO)
        decision = self.risk(
            ("opencode-go", agent.AvailabilityError("no key")),
            ("codex", agent.AvailabilityError("no login")),
            ("claude", claude),
        )
        self.assertEqual(decision.label, "auto")
        self.assertEqual(claude.calls, 4)

    def test_every_provider_unavailable_fails_closed_without_retrying_old_stages(self):
        stages = [("opencode-go", agent.AvailabilityError("a")), ("codex", agent.AvailabilityError("b")), ("claude", agent.AvailabilityError("c"))]
        self.assertEqual(self.risk(*stages).label, "manual")
        self.assertEqual(self.built, ["opencode-go", "codex", "claude"])
        with redirect_stderr(io.StringIO()), self.chain(*stages) as chat:
            with self.assertRaises(agent.ChainExhaustedError):
                agent.run_review(self.snap, "review this", "", chat)

    def test_valid_manual_vote_is_not_sent_to_a_fallback(self):
        decision = self.risk(("opencode-go", StubStage(MANUAL)), ("codex", StubStage(AUTO)), ("claude", StubStage(AUTO)))
        self.assertEqual(decision.label, "manual")
        self.assertEqual(self.built, ["opencode-go"])

    def test_malformed_primary_vote_does_not_fall_back(self):
        decision = self.risk(("opencode-go", StubStage({"submit_vote": {"label": "maybe"}})), ("codex", StubStage(AUTO)))
        self.assertEqual(decision.label, "manual")
        self.assertEqual(self.built, ["opencode-go"])

    def test_fatal_provider_error_does_not_fall_back(self):
        with redirect_stderr(io.StringIO()), self.chain(
            ("opencode-go", StubStage(error=agent.ProviderError("HTTP 400"))), ("codex", StubStage(AUTO))
        ) as chat:
            with self.assertRaises(agent.ProviderError):
                agent.run_review(self.snap, "review this", "", chat)
        self.assertEqual(self.built, ["opencode-go"])

    def test_valid_important_finding_from_codex_survives_without_building_claude(self):
        finding = {
            "class": "correctness",
            "symbol": "a.txt",
            "file": "a.txt",
            "line": 1,
            "body": "The value changed from old to new but readers still expect old.",
        }
        codex = StubStage(
            {
                "submit_findings": {"findings": [finding]},
                "submit_candidates": {"candidates": []},
                "submit_verify": {"results": [{"index": 1, "keep": True, "tag": "important"}, {"index": 2, "keep": True, "tag": "important"}]},
            }
        )
        claude = StubStage({"submit_findings": {"findings": []}, "submit_candidates": {"candidates": []}})
        with redirect_stderr(io.StringIO()), self.chain(("opencode-go", agent.AvailabilityError("quota")), ("codex", codex), ("claude", claude)) as chat:
            result = agent.run_review(self.snap, "review this", "", chat)
        kept = [(item.source, item.tag, item.cls, item.symbol, item.file, item.line) for item in result.findings]
        self.assertEqual(kept, [("code-review", "important", "correctness", "a.txt", "a.txt", 1)])
        self.assertTrue(result.summary.startswith("important 1, nit 0, pre-existing 0"))
        self.assertEqual(self.built, ["opencode-go", "codex"])
        self.assertEqual(codex.calls, 4)
        self.assertEqual(claude.calls, 0)


def http_error(code, body_error=None):
    def raise_error(*args, **kwargs):
        body = mock.Mock(wraps=io.BytesIO(b"{}"))
        if body_error is not None:
            body.read.side_effect = body_error
        raise urllib.error.HTTPError(agent.API_URL, code, "error", http.client.HTTPMessage(), body)

    return raise_error


class PrimaryAvailabilityTest(unittest.TestCase):
    def outcome(self, error):
        with mock.patch.object(agent.urllib.request, "urlopen", side_effect=error) as urlopen:
            try:
                agent.Chat("model", "key").next("session", [], [])
            except Exception as exc:
                return type(exc), urlopen.call_count
        return None, urlopen.call_count

    def test_missing_key_is_unavailable_and_malformed_key_is_fatal(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(agent.AvailabilityError):
                agent.Chat("model")
        with self.assertRaises(agent.RunnerError):
            agent.Chat("model", " key")

    def test_auth_quota_and_transport_failures_are_unavailable(self):
        self.assertEqual(self.outcome(http_error(401)), (agent.AvailabilityError, 1))
        self.assertEqual(self.outcome(http_error(402)), (agent.AvailabilityError, 1))
        self.assertEqual(self.outcome(http_error(503, TimeoutError("body read timed out"))), (agent.AvailabilityError, 2))
        self.assertEqual(self.outcome(http_error(429)), (agent.AvailabilityError, 2))
        self.assertEqual(self.outcome(http_error(529)), (agent.AvailabilityError, 2))
        self.assertEqual(self.outcome(urllib.error.URLError("down")), (agent.AvailabilityError, 2))

    def test_bad_request_and_policy_refusal_stay_fatal(self):
        self.assertEqual(self.outcome(http_error(400)), (agent.ProviderError, 1))
        self.assertEqual(self.outcome(http_error(403)), (agent.ProviderError, 1))


CODEX_LOGIN = {"OPENAI_API_KEY": "sk-in-login", "auth_mode": "chatgpt", "tokens": {"access_token": "access", "refresh_token": "refresh"}}
SECRETS = {
    "OPENCODE_API_KEY": "go-secret",
    "GH_TOKEN": "gh-secret",
    "GITHUB_TOKEN": "github-secret",
    "OPENAI_API_KEY": "openai-secret",
    "CODEX_API_KEY": "codex-secret",
    "ANTHROPIC_API_KEY": "anthropic-secret",
    "ANTHROPIC_AUTH_TOKEN": "anthropic-token",
    "ANTHROPIC_BASE_URL": "https://relay.invalid",
    "CODEX_AUTH_JSON": json.dumps(CODEX_LOGIN),
    "CLAUDE_CODE_OAUTH_TOKEN": "oauth-secret",
}
TOOLS = agent.READ_TOOLS + [agent._terminal_tool("submit_vote", "Submit.", {"label": {"type": "string"}}, ["label"])]
MESSAGES = [{"role": "system", "content": "system"}, {"role": "user", "content": "rate this change"}]


class NativeEnvelopeTest(unittest.TestCase):
    def test_only_offered_well_formed_calls_are_accepted(self):
        rejected = [
            {"content": "", "tool_calls": [terminal_call("run_shell", {})]},
            {"content": "", "tool_calls": [terminal_call("read_diff", {"scope": "pr"}), terminal_call("search", {"rev": "head", "literal": "x"})]},
            {"content": "", "tool_calls": [{"id": "a", "type": "function", "function": {"name": "submit_vote", "arguments": "[]"}}]},
            {"content": "", "tool_calls": [{"id": "a", "type": "function", "function": {"name": "submit_vote", "arguments": "{"}}]},
            {"content": "", "tool_calls": [], "extra": True},
            {"content": None, "tool_calls": []},
        ]
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(agent.RunnerError):
                agent._native_message(value, TOOLS, None)
        with self.assertRaises(agent.RunnerError):
            agent._native_message({"content": "", "tool_calls": [terminal_call("read_diff", {"scope": "pr"})]}, TOOLS, "submit_vote")
        with self.assertRaises(agent.RunnerError):
            agent._native_message({"content": "", "tool_calls": [terminal_call("submit_vote", {"label": "auto"})]}, [], None)
        final = {"content": '{"label": "auto"}', "tool_calls": []}
        self.assertEqual(agent._native_message(final, TOOLS, "submit_vote"), final)


class NativeClientTest(RepoCase):
    def setUp(self):
        super().setUp()
        self.fake = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.bin = self.fake / "bin"
        self.bin.mkdir()
        launch = " ".join(shlex.quote(part) for part in (sys.executable, str(FAKE_CLIENT), str(self.fake)))
        for name in ("codex", "claude"):
            script = self.bin / name
            script.write_text(f'#!/bin/sh\nexec {launch} "$0" "$@"\n', encoding="utf-8")
            script.chmod(0o755)
        home = self.fake / "home"
        home.mkdir()
        environ = dict(SECRETS, PATH=f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}", HOME=str(home))
        patcher = mock.patch.dict(os.environ, environ, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def plan(self, name, **plan):
        (self.fake / f"{name}.plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def log(self, name):
        path = self.fake / f"{name}.log"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def assert_scrubbed(self, entry):
        for key in SECRETS:
            if key != "CLAUDE_CODE_OAUTH_TOKEN":
                self.assertNotIn(key, entry["env"])
        for value in SECRETS.values():
            self.assertNotIn(value, " ".join(entry["argv"]))
            self.assertNotIn(value, entry["prompt"])
        self.assertEqual(entry["cwd_entries"], [])

    def test_codex_gets_the_conversation_and_an_isolated_chatgpt_login_for_the_whole_job(self):
        self.plan("codex", replies={"submit_vote": {"label": "auto"}})
        with agent.FallbackChat((("codex", agent.CodexChat),)) as chat:
            first = chat.next("s", MESSAGES, TOOLS)
            chat.next("s", MESSAGES, TOOLS)
        self.assertEqual(first["tool_calls"][0]["function"]["name"], "submit_vote")
        entries = self.log("codex")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["home"], entries[1]["home"])
        self.assertFalse(Path(entries[0]["home"]).exists())
        entry = entries[0]
        self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", entry["env"])
        self.assert_scrubbed(entry)
        self.assertEqual(entry["auth_mode"], 0o600)
        self.assertIsNone(entry["auth"]["OPENAI_API_KEY"])
        self.assertEqual(entry["auth"]["tokens"], CODEX_LOGIN["tokens"])
        argv = entry["argv"]
        for flag in ("--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
        disabled = {argv[index + 1] for index, arg in enumerate(argv) if arg == "--disable"}
        self.assertTrue({"shell_tool", "unified_exec", "apps", "plugins", "multi_agent", "hooks"} <= disabled)
        self.assertEqual(argv[-1], "-")
        self.assertIn("rate this change", entry["prompt"])

    def test_claude_runs_without_tools_user_settings_or_api_keys(self):
        self.plan("claude", replies={"submit_vote": {"label": "auto"}})
        with agent.FallbackChat((("claude", agent.ClaudeChat),)) as chat:
            message = chat.next("s", MESSAGES, TOOLS)
        self.assertEqual(message["tool_calls"][0]["function"]["name"], "submit_vote")
        entry = self.log("claude")[0]
        self.assert_scrubbed(entry)
        self.assertEqual(entry["env"]["CLAUDE_CODE_OAUTH_TOKEN"], "oauth-secret")
        argv = entry["argv"]
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "")
        for flag in ("-p", "--safe-mode", "--restricted", "--strict-mcp-config", "--no-session-persistence"):
            self.assertIn(flag, argv)
        self.assertNotIn("--bare", argv)
        (status,) = self.log("claude.auth")
        self.assert_scrubbed(status)
        self.assertEqual(status["argv"], ["auth", "status", "--json"])
        self.assertEqual(status["env"]["CLAUDE_CODE_OAUTH_TOKEN"], "oauth-secret")

    def native_outcome(self, cls, **plan):
        self.plan(cls.command, **plan)
        with tempfile.TemporaryDirectory() as root:
            try:
                cls(Path(root)).next("s", MESSAGES, TOOLS)
            except Exception as exc:
                return type(exc)
        return None

    def test_native_failures_are_classified_from_failure_signals_only(self):
        routing = {"type": "turn.failed", "error": {"message": "workspace routing discovery failed: Connection failed"}}
        odd = {"type": "turn.failed", "error": {"message": "the turn was cancelled"}}
        self.assertIs(self.native_outcome(agent.CodexChat, events=[routing], code=1), agent.AvailabilityError)
        self.assertIs(self.native_outcome(agent.CodexChat, events=[odd], code=1), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.CodexChat, message="not json"), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.CodexChat, code=1), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.CodexChat, code=2, stderr="error: unexpected argument '--bogus' found"), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.CodexChat, code=1, stderr="Error: stream disconnected before completion"), agent.AvailabilityError)
        quota_words = {"content": "", "tool_calls": [terminal_call("submit_vote", {"label": "rate limit quota 429"})]}
        self.assertIsNone(self.native_outcome(agent.CodexChat, message=quota_words))
        limit = {"type": "result", "subtype": "success", "is_error": True, "result": "Claude AI usage limit reached"}
        turns = {"type": "result", "subtype": "error_max_turns", "is_error": True, "result": ""}
        self.assertIs(self.native_outcome(agent.ClaudeChat, result=limit, code=1), agent.AvailabilityError)
        self.assertIs(self.native_outcome(agent.ClaudeChat, result=turns, code=1), agent.RunnerError)
        settings = "claude-launch: cannot create a settings file in /run: Operation not permitted"
        self.assertIs(self.native_outcome(agent.ClaudeChat, raw="", code=1, stderr=settings), agent.AvailabilityError)
        self.assertIs(self.native_outcome(agent.ClaudeChat, raw="", code=1, stderr="error: unknown option '--bogus'"), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.ClaudeChat, raw="", code=1, stderr="Error: --json-schema is not valid JSON"), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.ClaudeChat, raw="", code=1), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.ClaudeChat, message={"content": "", "tool_calls": [terminal_call("run_shell", {})]}), agent.RunnerError)
        trace = "error: invalid config value for model_reasoning_effort\n    at parse (config.toml line 529)"
        self.assertIs(self.native_outcome(agent.CodexChat, code=2, stderr=trace), agent.RunnerError)
        self.assertIs(self.native_outcome(agent.CodexChat, code=1, stderr="Error: unexpected status 503 from the responses endpoint"), agent.AvailabilityError)
        self.assertIs(self.native_outcome(agent.ClaudeChat, raw="", code=1, stderr="Error: invalid settings\n    at load (cli.js:529:13)"), agent.RunnerError)
        overloaded = {"type": "result", "subtype": "success", "is_error": True, "result": "API Error", "api_error_status": 529}
        self.assertIs(self.native_outcome(agent.ClaudeChat, result=overloaded, code=1), agent.AvailabilityError)

    def test_codex_content_and_output_stops_are_fatal_and_capacity_falls_back(self):
        def failed(message):
            return [{"type": "error", "message": message}, {"type": "turn.failed", "error": {"message": message}}]

        def chain_outcome(message):
            self.plan("codex", events=failed(message), code=1)
            self.plan("claude", replies=MANUAL)
            for log in ("claude.log", "claude.auth.log"):
                (self.fake / log).unlink(missing_ok=True)
            with redirect_stderr(io.StringIO()), agent.FallbackChat((("codex", agent.CodexChat), ("claude", agent.ClaudeChat))) as chat:
                try:
                    chat.next("s", MESSAGES, TOOLS)
                except Exception as exc:
                    return type(exc), len(self.log("claude")), len(self.log("claude.auth"))
            return None, len(self.log("claude")), len(self.log("claude.auth"))

        for reason in ("content_filter", "max_output_tokens"):
            message = f"stream disconnected before completion: Incomplete response returned, reason: {reason}"
            with self.subTest(message=message):
                self.assertIs(self.native_outcome(agent.CodexChat, events=failed(message), code=1), agent.RunnerError)
                self.assertEqual(chain_outcome(message), (agent.RunnerError, 0, 0))
        for message in (
            "Selected model is at capacity. Please try a different model.",
            "We\u2019re currently experiencing high demand, which may cause temporary errors.",
            "Your workspace is out of credits. Add credits to continue.",
            "You hit your spend cap set in your workspace. Increase your spend cap to continue.",
            "To use Codex with your ChatGPT plan, upgrade to Plus: https://chatgpt.com/explore/plus.",
        ):
            with self.subTest(message=message):
                self.assertIs(self.native_outcome(agent.CodexChat, events=failed(message), code=1), agent.AvailabilityError)
                self.assertEqual(chain_outcome(message), (None, 1, 1))

    def local_login(self):
        os.environ["CODEX_AUTH_JSON"] = ""
        source = Path(os.environ["HOME"]) / ".codex" / "auth.json"
        source.parent.mkdir(exist_ok=True)
        source.write_text(json.dumps({**CODEX_LOGIN, "last_refresh": "old", "extra": "kept"}), encoding="utf-8")
        source.chmod(0o644)
        return source

    def test_refreshed_local_codex_login_is_saved_back_privately(self):
        source = self.local_login()
        rotated = {"tokens": {"access_token": "access-2", "refresh_token": "refresh-2", "id_token": "id-2"}, "last_refresh": "new"}
        self.plan("codex", replies=AUTO, refresh=rotated)
        with tempfile.TemporaryDirectory() as root:
            chat = agent.CodexChat(Path(root))
            chat.next("s", MESSAGES, TOOLS)
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), {**CODEX_LOGIN, "extra": "kept", **rotated})
            self.assertEqual(source.stat().st_mode & 0o777, 0o600)
            self.assertEqual([path.name for path in source.parent.iterdir()], ["auth.json"])
            again = {"tokens": {"access_token": "access-3", "refresh_token": "refresh-3"}, "last_refresh": "newer"}
            routing = {"type": "turn.failed", "error": {"message": "workspace routing discovery failed: Connection failed"}}
            self.plan("codex", events=[routing], code=1, refresh=again)
            with self.assertRaises(agent.AvailabilityError):
                chat.next("s", MESSAGES, TOOLS)
        self.assertEqual(json.loads(source.read_text(encoding="utf-8")), {**CODEX_LOGIN, "extra": "kept", **again})
        self.assertEqual(source.stat().st_mode & 0o777, 0o600)

    def test_secret_codex_login_is_never_written_back(self):
        source = Path(os.environ["HOME"]) / ".codex" / "auth.json"
        source.parent.mkdir()
        source.write_text(json.dumps(CODEX_LOGIN), encoding="utf-8")
        before = source.stat().st_mtime_ns
        self.plan("codex", replies=AUTO, refresh={"tokens": {"access_token": "access-2", "refresh_token": "refresh-2"}})
        with mock.patch.object(agent, "_write_private") as write, tempfile.TemporaryDirectory() as root:
            agent.CodexChat(Path(root)).next("s", MESSAGES, TOOLS)
        write.assert_not_called()
        self.assertEqual(json.loads(source.read_text(encoding="utf-8")), CODEX_LOGIN)
        self.assertEqual(source.stat().st_mtime_ns, before)
        self.assertEqual([path.name for path in source.parent.iterdir()], ["auth.json"])

    def test_refreshed_login_never_overwrites_an_external_change_or_saves_a_malformed_one(self):
        rotated = {"tokens": {"access_token": "access-2", "refresh_token": "refresh-2"}}
        for refresh, external in ((rotated, '{"changed": true}'), ("{", None)):
            with self.subTest(refresh=refresh), tempfile.TemporaryDirectory() as root:
                source = self.local_login()
                self.plan("codex", replies=AUTO, refresh=refresh)
                chat = agent.CodexChat(Path(root))
                if external is not None:
                    source.write_text(external, encoding="utf-8")
                expected = source.read_text(encoding="utf-8")
                err = io.StringIO()
                with redirect_stderr(err):
                    chat.next("s", MESSAGES, TOOLS)
                self.assertEqual(source.read_text(encoding="utf-8"), expected)
                self.assertIn("was not", err.getvalue())
                self.assertNotIn("refresh-2", err.getvalue())
                self.assertNotIn("access", err.getvalue())

    def claude_outcome(self, auth, token=""):
        self.plan("claude", auth=auth, replies={"submit_vote": {"label": "auto"}})
        (self.fake / "claude.log").unlink(missing_ok=True)
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": token}), tempfile.TemporaryDirectory() as root:
            try:
                agent.ClaudeChat(Path(root)).next("s", MESSAGES, TOOLS)
            except Exception as exc:
                return type(exc), len(self.log("claude"))
        return None, len(self.log("claude"))

    def test_claude_needs_a_subscription_login_before_inference(self):
        subscription = {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "pro"}
        setup_token = {"loggedIn": True, "authMethod": "oauth_token", "apiProvider": "firstParty", "subscriptionType": None}
        self.assertEqual(self.claude_outcome({"status": subscription}), (None, 1))
        self.assertEqual(self.claude_outcome({"status": setup_token}, token="setup-token"), (None, 1))
        rejected = [
            ({"status": {**subscription, "authMethod": "api_key"}}, ""),
            ({"status": {**subscription, "authMethod": "console"}}, ""),
            ({"status": {**subscription, "apiProvider": "bedrock"}}, ""),
            ({"status": {**setup_token, "apiProvider": "vertex"}}, "setup-token"),
            ({"status": {"loggedIn": False, "authMethod": "none", "apiProvider": "firstParty"}, "code": 1}, ""),
            ({"status": {"loggedIn": True, "apiProvider": "firstParty"}}, ""),
            ({"status": {**subscription, "authMethod": "unknown"}}, ""),
            ({"status": subscription}, "setup-token"),
            ({"status": setup_token}, ""),
            ({"raw": "", "code": 1, "stderr": "cannot create a settings file: Operation not permitted"}, ""),
        ]
        for auth, token in rejected:
            with self.subTest(auth=auth, token=token):
                self.assertEqual(self.claude_outcome(auth, token), (agent.AvailabilityError, 0))

    def test_malformed_claude_auth_status_is_fatal_and_does_not_fall_back(self):
        for auth in ({"raw": "not json"}, {"raw": "[]"}, {"status": {"loggedIn": "yes"}}, {"raw": "", "code": 1, "stderr": "error: unknown command 'auth'"}):
            with self.subTest(auth=auth):
                self.assertEqual(self.claude_outcome(auth), (agent.RunnerError, 0))
        later = []
        self.plan("claude", auth={"raw": "not json"})
        with redirect_stderr(io.StringIO()), agent.FallbackChat((("claude", agent.ClaudeChat), ("later", later.append))) as chat:
            with self.assertRaises(agent.RunnerError):
                chat.next("s", MESSAGES, TOOLS)
        self.assertEqual(later, [])

    def test_missing_login_or_binary_is_unavailable_and_a_malformed_login_is_fatal(self):
        cases = [
            ({"CODEX_AUTH_JSON": ""}, agent.AvailabilityError),
            ({"CODEX_AUTH_JSON": json.dumps({"OPENAI_API_KEY": "sk"})}, agent.AvailabilityError),
            ({"CODEX_AUTH_JSON": "{"}, agent.RunnerError),
            ({"PATH": str(self.fake / "home")}, agent.AvailabilityError),
        ]
        for env, expected in cases:
            with self.subTest(env=env), mock.patch.dict(os.environ, env), tempfile.TemporaryDirectory() as root:
                with self.assertRaises(expected):
                    agent.CodexChat(Path(root))
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "bad token"}), tempfile.TemporaryDirectory() as root:
            with self.assertRaises(agent.RunnerError):
                agent.ClaudeChat(Path(root))

    def run_main(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = agent._main([*argv, "--repo", str(self.repo), "--base", self.base, "--head", self.head, "--from", self.base])
        return code, out.getvalue()

    def test_risk_vote_runs_on_codex_when_the_go_key_is_missing(self):
        del os.environ["OPENCODE_API_KEY"]
        self.plan("codex", replies=AUTO)
        self.plan("claude", replies=MANUAL)
        code, out = self.run_main("risk")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["label"], "auto")
        self.assertEqual(len(self.log("codex")), 4)
        self.assertEqual(self.log("claude"), [])

    def test_whole_chain_unavailable_makes_risk_manual_and_review_fail(self):
        del os.environ["OPENCODE_API_KEY"]
        os.environ["CODEX_AUTH_JSON"] = ""
        self.plan("claude", raw="", code=1, stderr="cannot create a settings file: Operation not permitted")
        code, out = self.run_main("risk")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["label"], "manual")
        self.assertEqual(len(self.log("claude")), 1)
        os.environ["REVIEW_PROMPT"] = "review this"
        code, out = self.run_main("review", "--prompt-env", "REVIEW_PROMPT")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
