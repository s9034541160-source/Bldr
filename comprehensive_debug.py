import sys
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting comprehensive debug of bldr_gui")
        import bldr_gui
        logger.info("Successfully imported bldr_gui")
        
        # Try to run the main function
        logger.info("Calling bldr_gui.main()")
        bldr_gui.main()
        logger.info("bldr_gui.main() completed successfully")
        
    except Exception as e:
        logger.error(f"Error running GUI: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()