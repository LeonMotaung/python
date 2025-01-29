from pymongo import MongoClient
from gridfs import GridFS
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
import pandas as pd
import json
from datetime import datetime

# Load environment variables
load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client.DataAnalysis
        self.fs = GridFS(self.db)
        
    def save_file(self, file, filename, user_id, file_type):
        """Save file to GridFS and metadata to files collection"""
        try:
            # Store the file in GridFS
            file_id = self.fs.put(
                file,
                filename=filename,
                user_id=user_id,
                upload_date=datetime.utcnow(),
                content_type=file_type
            )
            
            # Store metadata in files collection
            metadata = {
                'file_id': file_id,
                'filename': filename,
                'user_id': user_id,
                'upload_date': datetime.utcnow(),
                'content_type': file_type,
                'status': 'processed'
            }
            self.db.files.insert_one(metadata)
            
            return str(file_id)
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            raise
    
    def get_file(self, file_id):
        """Retrieve file from GridFS"""
        try:
            return self.fs.get(ObjectId(file_id))
        except Exception as e:
            print(f"Error retrieving file: {str(e)}")
            raise
    
    def save_analysis_results(self, file_id, summary_stats, visualizations):
        """Save analysis results to analysis_results collection"""
        try:
            result = {
                'file_id': ObjectId(file_id),
                'summary_stats': summary_stats,
                'visualizations': visualizations,
                'created_at': datetime.utcnow()
            }
            return self.db.analysis_results.insert_one(result)
        except Exception as e:
            print(f"Error saving analysis results: {str(e)}")
            raise
    
    def get_analysis_results(self, file_id):
        """Retrieve analysis results from analysis_results collection"""
        try:
            return self.db.analysis_results.find_one({'file_id': ObjectId(file_id)})
        except Exception as e:
            print(f"Error retrieving analysis results: {str(e)}")
            raise
    
    def get_user_files(self, user_id):
        """Get all files uploaded by a user"""
        try:
            return list(self.db.files.find({'user_id': user_id}))
        except Exception as e:
            print(f"Error retrieving user files: {str(e)}")
            raise
    
    def delete_file(self, file_id):
        """Delete file and its analysis results"""
        try:
            # Delete file from GridFS
            self.fs.delete(ObjectId(file_id))
            
            # Delete metadata from files collection
            self.db.files.delete_one({'file_id': ObjectId(file_id)})
            
            # Delete analysis results
            self.db.analysis_results.delete_one({'file_id': ObjectId(file_id)})
            
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            raise

    def record_login(self, email):
        """Record user login history"""
        try:
            login_record = {
                'email': email,
                'login_time': datetime.utcnow()
            }
            return self.db.login_history.insert_one(login_record)
        except Exception as e:
            print(f"Error recording login: {str(e)}")
            raise

    def get_login_history(self, email):
        """Get user's login history"""
        try:
            return list(self.db.login_history.find({'email': email}).sort('login_time', -1))
        except Exception as e:
            print(f"Error retrieving login history: {str(e)}")
            raise

# Create a singleton instance
mongodb = MongoDB()
