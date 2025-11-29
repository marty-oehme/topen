from pathlib import Path

from topen import parse_rc


class TestRcFile:
    def test_taskrc_parsing(self, fake_rc):
        fake_rc.write_text("""
        data.location=~/.taskies
        notes.dir=/there
        notes.ext=yaml
        notes.annot=Boo!
        notes.editor=micro
        notes.quiet=true
        """)
        rc_cfg = parse_rc(fake_rc)
        assert rc_cfg["task_data"] == Path("~/.taskies")
        assert rc_cfg["notes_dir"] == Path("/there")
        assert rc_cfg["notes_ext"] == "yaml"
        assert rc_cfg["notes_annot"] == "Boo!"
        assert rc_cfg["notes_editor"] == "micro"
        assert rc_cfg["notes_quiet"] is True

    def test_taskrc_parses_boolean_true(self, fake_rc):
        fake_rc.write_text("""
        notes.quiet=true
        """)
        rc_cfg = parse_rc(fake_rc)
        assert rc_cfg["notes_quiet"] is True

    def test_taskrc_parses_boolean_false(self, fake_rc):
        fake_rc.write_text("""
        notes.quiet=false
        """)
        rc_cfg = parse_rc(fake_rc)
        assert rc_cfg["notes_quiet"] is False
