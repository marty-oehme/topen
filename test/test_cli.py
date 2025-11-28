from topen import parse_cli


class TestCli:
    def test_cli_minimum_id(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["topen", "42"])
        assert parse_cli() == {"task_id": "42"}
