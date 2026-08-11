import unittest
from unittest.mock import patch, MagicMock
from backend.parsers import extract_urls_from_text, expand_google_maps_url


class TestParsers(unittest.TestCase):
    def test_extract_urls_from_text(self):
        sample_text = """
        Hôm nay đi ăn ở mấy quán này nhé:
        1. https://maps.app.goo.gl/AbCdEfGh12345
        2. Quán phở ngon: https://www.google.com/maps/place/Pho+Thin/@21.028511,105.854444,17z
        3. Link lặp lại: https://maps.app.goo.gl/AbCdEfGh12345
        """
        urls = extract_urls_from_text(sample_text)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://maps.app.goo.gl/AbCdEfGh12345", urls)
        self.assertIn("https://www.google.com/maps/place/Pho+Thin/@21.028511,105.854444,17z", urls)

    @patch('backend.parsers.requests.get')
    def test_expand_google_maps_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.url = "https://www.google.com/maps/place/Pho+Thin"
        mock_get.return_value = mock_response

        short_url = "https://maps.app.goo.gl/AbCdEfGh12345"
        expanded = expand_google_maps_url(short_url)
        self.assertEqual(expanded, "https://www.google.com/maps/place/Pho+Thin")


if __name__ == "__main__":
    unittest.main()
