import unittest

from jobfit.analyzer import analyze_match


class AnalyzerTests(unittest.TestCase):
    def test_matches_skills_and_flags_missing(self):
        report = analyze_match(
            "Навыки: Python, MATLAB. Ищу частичную занятость 20 часов в неделю.",
            "Важно знать Python, SQL и Git. Полная занятость, график 5/2.",
        )
        self.assertIn("Python", report.matched_skills)
        self.assertIn("SQL", report.missing_skills)
        self.assertIn("Git", report.missing_skills)
        self.assertTrue(report.schedule_risks)

    def test_flags_claim_not_supported_by_resume(self):
        report = analyze_match(
            "Навыки: Python.",
            "Требуется Python и Git.",
            "Работаю с Python и GitHub.",
        )
        self.assertEqual(report.unsupported_claims, ["Git"])

    def test_cover_letter_uses_detected_evidence(self):
        report = analyze_match("Python и C++", "Нужны Python и C++")
        self.assertIn("Python", report.cover_letter)
        self.assertIn("C++", report.cover_letter)

    def test_cover_letter_title_has_clean_punctuation(self):
        report = analyze_match("Навыки: Python", "AI-стажер. Нужен Python.")
        self.assertIn("позиция «AI-стажер»", report.cover_letter)
        self.assertNotIn("AI-стажер.»", report.cover_letter)


if __name__ == "__main__":
    unittest.main()

