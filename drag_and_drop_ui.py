from data_indexer import DataIndexer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def upload_and_index(file_path):
    '''
        Function to handle file indexing after upload.
    '''
    try:
        logging.info(f"Indexing file: {file_path}")
        indexer = DataIndexer(file_path)
        indexer.on_upload(output_folder="raw_data_extracted")
        total_rows = indexer.get_total_rows()
        logging.info(f"Indexing complete. Total rows indexed: {total_rows}")
    except Exception as e:
        # Fix: Ensure no invalid arguments are passed to the logger
        logging.error(f"Error during indexing: {e}")
        raise

def main():
    """
    Handle the drag-and-drop upload and indexing process.
    """
    def on_progress(current, total):
        """Update the progress bar and label."""
        progress_var.set((current / total) * 100)
        progress_label.config(text=f"Progress: {current}/{total} documents")
        root.update_idletasks()  # Ensure UI updates in real-time

    def on_file_drop(event):
        """Handle the file drop event."""
        file_path = event.data

        # Initialize DataIndexer and process the file
        try:
            progress_label.config(text="Processing...")
            progress_bar.start()  # Start the progress bar animation

            indexer = DataIndexer(file_path)
            logging.info(f"File dropped: {file_path}")
            logging.info("Starting indexing process...")
            indexer.on_upload(output_folder="raw_data_extracted", progress_callback=on_progress)

            # Ensure all rows are processed and indexed
            total_rows = indexer.get_total_rows()
            print(f"Total Rows: {total_rows}")  # Debugging: Log total rows
            progress_label.config(text="Indexing Complete!")
        except Exception as e:
            # Log the error for debugging
            print(f"Error during indexing: {e}")
            progress_label.config(text=f"Error: {e}")
        finally:
            progress_bar.stop()  # Stop the progress bar animation

    def disable_default_behavior(event):
        """Prevent default behavior of unintended events."""
        return "break"

    # Create the drag-and-drop modal
    root = tk.Tk()
    root.title("Upload and Index")
    root.geometry("400x200")

    drop_label = tk.Label(root, text="Drag and drop your file here", relief="solid", height=5)
    drop_label.pack(pady=20, padx=20, fill="both", expand=True)

    # Bind drag-and-drop event
    drop_label.bind("<Drop>", on_file_drop)

    # Prevent unintended events from triggering
    drop_label.bind("<Button-1>", disable_default_behavior)
    drop_label.bind("<Double-1>", disable_default_behavior)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(pady=10, padx=20, fill="x")

    progress_label = tk.Label(root, text="")
    progress_label.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
