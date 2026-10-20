import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "ci" / "opencode_agent.py"
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


if __name__ == "__main__":
    unittest.main()
