import tempfile
import unittest
from pathlib import Path

from lowcode_agent_kit.skill_installer import install


ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_copy_selected_generic_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            result = install(ROOT, target, ["eap-obpm"], method="copy")
            self.assertEqual(result, [("eap-obpm", "copy")])
            self.assertTrue((target / "lowcode-eap-obpm" / "SKILL.md").is_file())
            self.assertFalse((target / "lowcode-extn").exists())

    def test_link_and_idempotent_repeat(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            self.assertEqual(install(ROOT, target, ["extn"], method="link"), [("extn", "link")])
            self.assertEqual(install(ROOT, target, ["extn"], method="link"), [("extn", "already-linked")])
            self.assertTrue((target / "lowcode-extn").is_symlink())

    def test_dry_run_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            self.assertEqual(install(ROOT, target, ["cloudfile"], dry_run=True), [("cloudfile", "would-link")])
            self.assertFalse(target.exists())

    def test_existing_installed_skill_is_protected(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            existing = target / "lowcode-eap-obpm"
            existing.mkdir(parents=True)
            (existing / "custom.txt").write_text("leave alone")
            with self.assertRaises(FileExistsError):
                install(ROOT, target, ["eap-obpm"])
            self.assertEqual((existing / "custom.txt").read_text(), "leave alone")

    def test_invalid_skill_does_not_create_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "skills"
            with self.assertRaises(ValueError):
                install(ROOT, target, ["not-an-adapter"])
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
