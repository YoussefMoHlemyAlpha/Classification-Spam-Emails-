import time
from gmail_filter import classify_and_filter_emails

def job():
    print("Running spam classification job...")
    try:
        classify_and_filter_emails()
        print(" Job completed successfully.")
    except Exception as e:
        print(f"Error during job: {e}")

if __name__ == "__main__":
    print("Gmail spam filter started...")

    while True:
        job() 
        print("Sleeping for 6 hours...")
        time.sleep(6 * 60 * 60)  
