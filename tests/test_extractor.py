import unittest
from unittest.mock import patch, MagicMock
from PIL import Image
from src.doc_extractor import extract_document_data
from src.instructor_client import DocumentMetadata

class TestDocumentExtractor(unittest.TestCase):

    def setUp(self):
        # Create mock images
        self.images = []
        for i in range(3):
            img = Image.new('RGB', (100, 100), color='white')
            self.images.append(img)
        self.segments = [(0,1), (2,2)]  # Two documents: pages [0-1], and page [2]

    @patch('src.doc_extractor.base64.b64encode', return_value=b'fake_b64')
    def test_extract_document_data(self, mock_b64encode):
        mock_instructor_client = MagicMock()

        # We expect `extract_metadata` to be called twice (once per doc segment)
        # Return a fake DocumentMetadata object for each call
        fake_meta_1 = DocumentMetadata(
            title="Doc1 Title",
            date="2022-01-01",
            summary="Summary of doc1",
            tags=["tag1", "tag2"]
        )
        fake_meta_2 = DocumentMetadata(
            title="Doc2 Title",
            date="2023-02-02",
            summary="Summary of doc2",
            tags=["tagA"]
        )
        mock_instructor_client.extract_metadata.side_effect = [fake_meta_1, fake_meta_2]

        result = extract_document_data(mock_instructor_client, self.images, self.segments)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].title, "Doc1 Title")
        self.assertEqual(result[1].title, "Doc2 Title")

        # Check that the client was called twice (once per segment)
        self.assertEqual(mock_instructor_client.extract_metadata.call_count, 2)


if __name__ == '__main__':
    unittest.main()
