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
    def __init__(self, file_path: str = None, data_file: str = "data.json"):
        """
        Initialize the DataIndexer with the path to the Excel file or load data from a file.
        If file_path is None, the instance is initialized for FAISS index loading only.
        """
        if file_path:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"The file {file_path} does not exist.")
            self.file_path = file_path
        else:
            self.file_path = None  # Allow initialization without a file path for FAISS loading

        self.data_file = data_file
        self.data = None
        self.index = None
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Pre-trained model for embeddings

        # Load data if the data file exists
        if os.path.exists(self.data_file):
            logging.info(f"Loading data from {self.data_file}...")
            try:
                with open(self.data_file, "r") as f:
                    self.data = pd.DataFrame(json.load(f))
                logging.info("Data loaded successfully.")
            except Exception as e:
                logging.error(f"Error loading data from {self.data_file}: {e}")
                raise
        else:
            logging.warning(f"No data file found at {self.data_file}. Data will not be loaded.")

        logging.info(f"DataIndexer initialized. File path: {self.file_path if self.file_path else 'None'}")

    def read_excel(self):
        """
        Read the Excel file into a pandas DataFrame and handle NaTType values.
        """
        try:
            logging.info(f"Reading Excel file: {self.file_path}")
            self.data = pd.read_excel(self.file_path, dtype=str)  # Read all columns as strings to avoid type issues
            logging.info(f"Loaded {len(self.data)} rows from {self.file_path}.")
            # Handle NaTType and null values immediately after loading the data
            self.handle_nat_values()
        except Exception as e:
            logging.error(f"Error reading Excel file: {e}")
            raise ValueError(f"Error reading Excel file: {e}")

    def handle_nat_values(self):
        """
        Replace NaTType, null values, and datetime objects with JSON-serializable values.
        """
        if self.data is not None:
            logging.info("Handling NaTType and null values in the data.")
            # Replace NaTType and NaN with an empty string
            self.data = self.data.where(pd.notnull(self.data), "").fillna("")
            # Ensure datetime columns are converted to strings
            for column in self.data.select_dtypes(include=["datetime"]).columns:
                self.data[column] = self.data[column].astype(str)
            logging.info("NaTType and null values handled successfully.")

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
        try:
            jsons_data = self.data.to_dict(orient="records")
            if not jsons_data:
                raise ValueError("No data found in the DataFrame.")
            logging.info(f"Converted {len(jsons_data)} rows to JSON format.")
            return jsons_data
        except Exception as e:
            logging.error(f"Error converting data to JSON: {e}")
            raise ValueError(f"Error converting data to JSON: {e}")

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
        The filename format will be row_appID_APP_NAME.json.
        """
        if self.data is None:
            raise ValueError("No data loaded. Please call read_excel() first.")
        
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)

        json_data = self.convert_to_json()

        # Now write JSON data to files
        for i, row in enumerate(json_data):
            # Extract App ID and APP NAME for the filename
            app_id = row.get("App ID", "unknown")
            app_name = row.get("APP NAME", "unknown").replace(" ", "_").replace("/", "_")
            file_name = f"row_{app_id}_{app_name}.json"
            file_path = os.path.join(output_folder, file_name)

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

            # Step 3: Save the data to a file for future use
            with open(self.data_file, "w") as f:
                json.dump(self.data.to_dict(orient="records"), f, indent=4)
            logging.info(f"Data saved to {self.data_file}.")

            # Step 4: Index the data into FAISS
            print("Starting to index the data into FAISS...")
            self.index_faiss(progress_callback)
            print("Data processing and indexing completed.")

            # Step 5: Save the FAISS index to a file
            faiss_index_file = "faiss_index.bin"
            faiss.write_index(self.index, faiss_index_file)
            logging.info(f"FAISS index saved to {faiss_index_file}.")
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
