import pandas as pd
import os
import json
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import faiss
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class DataIndexer:
    def __init__(self, file_path: str):
        """
        Initialize the DataIndexer with the path to the Excel file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        self.file_path = file_path
        self.data = None
        self.index = None
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Pre-trained model for embeddings
        logging.info(f"DataIndexer initialized with file: {file_path}")

    def read_excel(self):
        """
        Read the Excel file into a pandas DataFrame and handle NaTType values.
        """
        try:
            self.data = pd.read_excel(self.file_path)
            print(f"Loaded {len(self.data)} rows from {self.file_path}.")
            # Handle NaTType and null values immediately after loading the data
            self.handle_nat_values()
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

    def handle_nat_values(self):
        """
        Replace NaTType, null values, and datetime objects with JSON-serializable values.
        """
        if self.data is not None:
            # Replace NaTType and NaN with an empty string
            self.data = self.data.where(pd.notnull(self.data), "").fillna("")
            # Ensure datetime columns are converted to strings
            for column in self.data.select_dtypes(include=["datetime", "object"]).columns:
                self.data[column] = self.data[column].apply(
                    lambda x: x.strftime("%Y-%m-%d") if isinstance(x, pd.Timestamp) and not pd.isnull(x) else ""
                )

    def get_cleaned_data(self):
        """
        Return the cleaned data as a list of dictionaries.
        """
        if self.data is not None:
            return self.data.to_dict(orient="records")
        return []

    def convert_to_json(self) -> List[Dict]:
        """
        Convert each row of the DataFrame into a JSON object.
        Returns a list of JSON objects.
        """
        if self.data is None:
            raise ValueError("No data loaded. Please call read_excel() first.")
        jsons_data = self.data.to_dict(orient="records")
        if not jsons_data:
            raise ValueError("No data found in the DataFrame.")
        else:
            print(f"Converted {len(jsons_data)} rows to JSON format.")
        return jsons_data

    def save_json(self, output_path: str):
        """
        Save the JSON objects to a file.
        """
        json_data = self.convert_to_json()
        try:
            with open(output_path, "w") as f:
                json.dump(json_data, f, indent=4)
        except Exception as e:
            raise ValueError(f"Error saving JSON file: {e}")

    def save_rows_to_folder(self, output_folder: str = "raw_data_extracted"):
        """
        Save each row of the DataFrame as a separate JSON file in the specified folder.
        """
        if self.data is None:
            raise ValueError("No data loaded. Please call read_excel() first.")
        
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)

        json_data = self.convert_to_json()

        # Now write JSON data to files
        for i, row in enumerate(json_data):
            file_path = os.path.join(output_folder, f"row_{i + 1}.json")
            try:
                with open(file_path, "w") as f:
                    json.dump(row, f, indent=4)
            except Exception as e:
                raise ValueError(f"Error saving JSON file {file_path}: {e}")
        print(f"Saved {len(json_data)} rows to folder: {output_folder}")
        

    def index_faiss(self, progress_callback=None):
        """
        Index the JSON data into FAISS for similarity search with progress tracking.
        """
        if self.data is None:
            raise ValueError("No data loaded. Please call read_excel() first.")
        
        # Handle NaTType values
        self.handle_nat_values()

        # Debugging: Ensure no NaTType values remain
        if self.data.isnull().values.any():
            raise ValueError("Data contains null values after handling NaTType. Please check the input data.")

        # Get cleaned data
        cleaned_data = self.get_cleaned_data()

        # Extract text data for embeddings
        try:
            texts = [json.dumps(row) for row in cleaned_data]  # Use JSON strings as documents
        except TypeError as e:
            raise ValueError(f"Error serializing data to JSON: {e}")

        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_tensor=False)

        # Create FAISS index
        dimension = embeddings[0].shape[0]
        self.index = faiss.IndexFlatL2(dimension)

        # Add embeddings to the index with progress tracking
        for i, embedding in enumerate(embeddings):
            self.index.add(embedding.reshape(1, -1))
            if progress_callback:
                progress_callback(i + 1, len(embeddings))  # Update progress

        print(f"Indexed {len(embeddings)} documents into FAISS.")

    def search_faiss(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search the FAISS index for the top_k most similar documents to the query.
        Returns the corresponding JSON objects.
        """
        if self.index is None:
            raise ValueError("FAISS index is not built. Please call index_faiss() first.")
        
        # Generate embedding for the query
        query_embedding = self.model.encode([query], convert_to_tensor=False)

        # Perform search
        distances, indices = self.index.search(query_embedding, top_k)

        # Retrieve the corresponding JSON objects
        json_data = self.convert_to_json()
        results = [json_data[idx] for idx in indices[0] if idx < len(json_data)]

        return results

    def on_upload(self, output_folder: str = "raw_data_extracted", progress_callback=None):
        """
        Triggered after a file is uploaded. Automatically processes and indexes the data.
        """
        try:
            logging.info("File uploaded. Starting processing and indexing...")
            self.process_and_index(output_folder, progress_callback)
        except Exception as e:
            logging.error(f"Error during process_and_index: {e}")
            raise

    def process_and_index(self, output_folder: str = "raw_data_extracted", progress_callback=None):
        """
        Complete workflow: read Excel, save rows as JSON files, and index the data.
        """
        try:
            # Step 1: Read the Excel file
            logging.info("Starting to read the Excel file...")
            self.read_excel()  # `handle_nat_values` is now called within `read_excel`
            logging.info("Excel file read successfully.")

            # Step 2: Save rows as individual JSON files
            logging.info("Starting to save rows as JSON files...")
            self.save_rows_to_folder(output_folder)
            logging.info("Rows saved successfully.")

            # Step 3: Index the data into FAISS
            print("Starting to index the data into FAISS...")
            self.index_faiss(progress_callback)
            print("Data processing and indexing completed.")
        except Exception as e:
            logging.error(f"Error during process_and_index: {e}")
            raise

    def get_total_rows(self):
        """
        Returns the total number of rows in the data.
        Assumes the data is loaded into a DataFrame or similar structure.
        """
        if hasattr(self, 'data') and self.data is not None:
            return len(self.data)
        else:
            raise ValueError("Data is not loaded. Ensure the file is read before calling this method.")
