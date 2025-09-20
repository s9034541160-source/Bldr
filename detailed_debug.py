import sys
import traceback
import logging

# Set up logging to a file
logging.basicConfig(
    filename='gui_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting detailed debug of bldr_gui")
        print("Starting detailed debug of bldr_gui")
        
        import bldr_gui
        logger.info("Successfully imported bldr_gui")
        print("Successfully imported bldr_gui")
        
        # Try to run the main function
        logger.info("Calling bldr_gui.main()")
        print("Calling bldr_gui.main()")
        bldr_gui.main()
        logger.info("bldr_gui.main() completed successfully")
        print("bldr_gui.main() completed successfully")
        
    except Exception as e:
        error_msg = f"Error running GUI: {e}"
        traceback_msg = traceback.format_exc()
        
        logger.error(error_msg)
        logger.error(traceback_msg)
        print(error_msg)
        print(traceback_msg)
        
        # Also write to a file for easier reading
        with open('error_details.txt', 'w', encoding='utf-8') as f:
            f.write(f"{error_msg}\n\n{traceback_msg}")
        
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()