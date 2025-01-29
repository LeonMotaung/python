import unittest
from app import app
import os
import pandas as pd

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create test data
        self.test_data = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        self.test_csv = 'test.csv'
        self.test_data.to_csv(os.path.join('uploads', self.test_csv), index=False)

    def tearDown(self):
        # Clean up test files
        test_files = [
            os.path.join('uploads', self.test_csv),
            os.path.join('uploads', f'{self.test_csv}.pdf'),
            os.path.join('static', 'images', f'{self.test_csv}.png')
        ]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_upload_file(self):
        with open(os.path.join('uploads', self.test_csv), 'rb') as f:
            response = self.client.post(
                '/upload',
                data={'file': (f, self.test_csv)},
                content_type='multipart/form-data'
            )
            self.assertEqual(response.status_code, 302)  # Redirect status code

if __name__ == '__main__':
    unittest.main()
