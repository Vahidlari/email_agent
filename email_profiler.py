import getpass
import os
from typing import List, Dict
import json
import time
import sys
import select
import tty
import termios
from dotenv import load_dotenv
import logging
from dataclasses import dataclass, field

from ragora.utils import (
    EmailProvider,
    EmailProviderFactory,
    IMAPCredentials,
    ProviderType,
    EmailDraft,
)

from ragora.core import KnowledgeBaseManager, SearchStrategy, EmailPreprocessor, EmailMessageModel, EmailListResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmailSummary:
    message_id: str = field(default_factory=str)
    subject: str = field(default_factory=str)
    sender: str = field(default_factory=str)
    date_sent: str = field(default_factory=str)
    folder: str = field(default_factory=str)
    body: str = field(default_factory=str)

    def from_dict(self, data: Dict) -> 'EmailSummary':
        return EmailSummary(
            message_id=data["email_id"],
            subject=data["subject"],
            sender=data["sender"],
            date_sent=data["date_sent"],
            folder=data["folder"],
            body=data["body"] if data["body"] is not None else field(default_factory=str)
        )


def wait_with_quit(timeout_seconds: int) -> bool:
    """Wait up to timeout_seconds while allowing user to press 'q' to quit.

    Returns True if quit was requested, False otherwise.
    """
    # If stdin is not a TTY (e.g., running as a service), fall back to sleep
    if not sys.stdin.isatty():
        time.sleep(timeout_seconds)
        return False

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        # Put terminal into cbreak mode to read single characters without Enter
        tty.setcbreak(fd)
        end_time = time.time() + timeout_seconds
        print("Press 'q' to quit, waiting...")
        while time.time() < end_time:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
            if rlist:
                ch = sys.stdin.read(1)
                if ch.lower() == 'q':
                    return True
            # Small sleep granularity handled by select timeout
        return False
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def get_user_credentials_from_file():
    """Get email credentials from a .env file."""
    # load the .env file
    load_dotenv()
    # get the email, password and recipient from the .env file
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    recipient = os.getenv("RECIPIENT")
    return email, password, recipient


def get_weaviate_url_from_file():
    """Get Weaviate URL from a .env file."""
    # load the .env file
    load_dotenv()
    # get the weaviate_url from the .env file
    weaviate_url = os.getenv("WEAVIATE_URL")
    return weaviate_url


def get_user_credentials():
    """Get email credentials from user input."""
    print("=== Email Credentials Setup ===")
    # if credentials are provided in the .env file, use them
    email, password, recipient = get_user_credentials_from_file()
    if email and password:
        return email, password, recipient

    # Get Gmail address
    email = input("Enter your Gmail address: ").strip()
    if not email.endswith("@gmail.com"):
        print(
            "Warning: This example is configured for Gmail. Other providers may need different settings."
        )

    # Get password (hidden input)
    password = getpass.getpass("Enter your Gmail app password: ")
    print("password: ", password)

    # Get recipient email
    recipient = input("Enter recipient email address: ").strip()

    return email, password, recipient


def example_email_database_creation():
    """This function is used to create an email database using the KnowledgeBaseManager."""

    # Create email database
    kbm.create_collection(collection)

    # Get Weaviate URL from .env file or use default
    weaviate_url = get_weaviate_url_from_file() or "http://localhost:8080"

    # Initialize Knowledge Base Manager
    kbm = KnowledgeBaseManager(weaviate_url=weaviate_url)

    try:
        # Connect to email servers
        provider.connect()
        print("Connected to email servers")

        # Process emails from inbox and store in knowledge base
        print("\nProcessing emails from INBOX...")
        print(
            "Note: Email chunks will include full metadata (subject, sender, recipient, etc.)"
        )
        print(
            "      and support custom metadata for enhanced filtering and organization."
        )
        stored_ids = kbm.process_email_account(
            email_provider=provider, folder="INBOX", collection="Email"
        )
        print(f"Stored {len(stored_ids)} email chunks in knowledge base")

        # Search for emails
        print("\nSearching for emails about 'meeting'...")
        results = kbm.search("meeting", collection="Email", top_k=3)
        print(f"Found {results.total_found} relevant emails")

        for i, result in enumerate(results.results, 1):
            print(f"\n{i}. {result.get('subject', 'No subject')}")
            print(f"   Sender: {result.get('sender', 'Unknown')}")
            print(f"   Content preview: {result.get('content', '')[:100]}...")

        new_emails_info = kbm.check_new_emails(
            email_provider=provider,
            folder="INBOX",
            include_body=True,
            limit=5,
        )

        if new_emails_info["count"] > 0:
            # Process unread emails only
            print("\n\nProcessing new unread emails...")
            new_stored = kbm.process_new_emails(
                email_provider=provider,
                email_ids=[
                    email["email_id"] for email in new_emails_info["emails"][:3]
                ],
                collection="Email",
            )
            print(f"Stored {len(new_stored)} new email chunks")
        else:
            print("No new emails found")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        provider.disconnect()
        print("\nDisconnected from email servers")


def email_database_creation(
    emailProfile: EmailProvider, 
    kbm: KnowledgeBaseManager, 
    whitelist: List[str] = None, 
    blacklist: List[str] = None, 
    collection: str = "Email"
) -> None:
    """This function is used to create an email database using the KnowledgeBaseManager."""

    if whitelist is not None and blacklist is not None:
        raise ValueError("Whitelist and blacklist cannot be used together")
    try:
        # Connect to email servers
        emailProfile.connect()
        logger.info("Connected to email servers")

        # Fetch emails
        emails = emailProfile.fetch_messages(
            limit=None, folder=None, unread_only=False
        )

        filtered_email_ids = []
        if whitelist is None and blacklist is None:
            filtered_email_ids = [email_msg.message_id for email_msg in emails]
        elif whitelist is not None:
            filtered_email_ids = [email_msg.message_id for email_msg in emails if email_msg.sender.email in whitelist]
        else: # only blacklist is not None
            filtered_email_ids = [email_msg.message_id for email_msg in emails if email_msg.sender.email not in blacklist]

        stored_ids = kbm.process_new_emails(
            email_provider=emailProfile, 
            email_ids=filtered_email_ids, 
            collection=collection
        )

        # Disconnect from email servers
        emailProfile.disconnect()      
        logger.info(f"Stored {len(stored_ids)} email chunks in knowledge base")

    except Exception as e:
        logger.error(f"Error processing emails: {e}")
        raise e


def example_email_answer_drafting_workflow():
    """Example workflow for LLM-based answer drafting using email knowledge base."""
    print("=== Email Answer Drafting Workflow Example ===")

    from ragora import KnowledgeBaseManager, SearchStrategy

    # Get credentials
    try:
        email, password, recipient = get_user_credentials()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return

    # Create IMAP credentials
    credentials = IMAPCredentials(
        imap_server="imap.gmail.com",
        imap_port=993,
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        username=email,
        password=password,
        use_ssl=True,
        use_tls=False,
    )

    # Create provider
    provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)

    # Get Weaviate URL from .env file or use default
    weaviate_url = get_weaviate_url_from_file() or "http://localhost:8080"

    # Initialize Knowledge Base Manager
    kbm = KnowledgeBaseManager(weaviate_url=weaviate_url)

    try:
        # Step 1: Check for new emails (read-only, includes body for LLM)
        print("\nStep 1: Checking for new emails...")
        new_emails_info = kbm.check_new_emails(
            email_provider=provider, folder="INBOX", include_body=True, limit=5
        )
        print(f"Found {new_emails_info['count']} new emails")

        # Step 2: For each email, find relevant context from knowledge base
        print("\nStep 2: Finding relevant context for drafting replies...")
        for email_data in new_emails_info["emails"][:3]:  # Process first 3
            print(f"\n--- Processing: {email_data['subject']} ---")
            print(f"From: {email_data['sender']}")

            # Search for relevant context in knowledge base
            query = email_data["subject"] + " " + email_data.get("body", "")[:100]
            context_results = kbm.search(query=query, collection="Email", top_k=2)

            print(f"Found {context_results.total_found} relevant context items")
            for i, context in enumerate(context_results.results, 1):
                print(f"  {i}. {context.get('subject', 'No subject')}")

            # In a real scenario, this would be passed to an LLM
            print("  → LLM would draft reply using this context")
            print("  → Draft would be created using EmailProvider")
            print("  → User would review and send")

        # Step 3: After handling emails, index them in knowledge base
        print("\n\nStep 3: Indexing processed emails...")
        # Extract email IDs from the emails we processed
        processed_email_ids = [
            email["email_id"] for email in new_emails_info["emails"][:3]
        ]
        stored_ids = kbm.process_new_emails(
            email_provider=provider, email_ids=processed_email_ids, collection="Email"
        )
        print(f"Indexed {len(stored_ids)} email chunks")

        print("\nWorkflow complete!")
        print(
            "Note: Actual LLM integration and email sending would happen in your application"
        )

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


def initialize_email_profile():
    """Initialize email profile."""
    try:
        email, password, recipient = get_user_credentials()
        credentials = IMAPCredentials(
            imap_server="imap.gmail.com",
            imap_port=993,
            smtp_server="smtp.gmail.com",
            smtp_port=465,
            username=email,
            password=password,
            use_ssl=True,
            use_tls=False,
        )
        return EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)
    except Exception as e:
        logger.error(f"Error initializing email profile: {e}")
        raise e

def initialize_knowledge_base_manager():
    """Initialize knowledge base manager."""
    try:
        weaviate_url = get_weaviate_url_from_file() or "http://localhost:8080"
        kbm = KnowledgeBaseManager(weaviate_url=weaviate_url)
        logger.info("Knowledge base manager initialized")
        return kbm
    except Exception as e:
        logger.error(f"Error initializing knowledge base manager: {e}")
        raise e


def load_email_assistant_config(config: str) -> Dict:
    """ Load a JSON config file for the email assistant.
    The config file should contain the following fields:
    - whitelist: List[str]
    - blacklist: List[str]
    - collection: str
    - answer_patterns:
        - sender_email: str
        - answer_pattern: str
    """
    try:
        with open(config, 'r') as f:
            config = json.load(f)
        logger.info("Email assistant config loaded")
        return config
    except Exception as e:
        logger.error(f"Error loading email assistant config: {e}")
        raise e


def load_latex_file(latex_file: str, kbm: KnowledgeBaseManager, collection: str = "document") -> None:
    """ Load a LaTeX file into the knowledge base.
    """
    try:
        # read the latex file
        kbm.preprocess_document(latex_file, collection=collection)
    except Exception as e:
        logger.error(f"Error loading LaTeX file: {e}")
        raise e


def send_answer_to_email(
    email_profile: EmailProvider,
    email_message: EmailSummary,
    answer: str,
) -> bool:
    """ Send the answer to the email message.
    """
    try:
        subject = "RE: " + email_message.subject
        # Send message directly
        success = email_profile.send_message_direct(
            to=email_message.sender,
            subject=subject,
            body=answer,
        )
        return success
    except Exception as e:
        logger.error(f"Error sending answer to email: {e}")
        raise e


def draft_answer_for_email(
    email_profile: EmailProvider,
    email_message: EmailSummary,
    answer: str,
) -> EmailDraft:
    """ Draft an answer for the email message.
    """
    try:
        # Draft message
        draft = email_profile.create_draft(
            to=email_message.sender,
            subject="RE: " + email_message.subject,
            body=answer,
        )
        logger.info(f"Drafted answer for email: {email_message.message_id}, Subject: {email_message.subject}")
        return draft
    except Exception as e:
        logger.error(f"Error drafting answer for email: {e}")
        raise e


def check_new_emails(
    email_profile: EmailProvider, 
    kbm: KnowledgeBaseManager, 
    collection: str = "Email",
    limit: int = 5,
    whitelist: List[str] = None,
    blacklist: List[str] = None,
) -> List[EmailMessageModel]:
    """ Check for new emails in the email profile.
    """
    if whitelist is not None and blacklist is not None:
        raise ValueError("Whitelist and blacklist cannot be used together")
    try:
        new_emails = kbm.check_new_emails(email_profile, limit=limit, include_body=True)

        filtered_emails = []
        if whitelist is None and blacklist is None:
            filtered_emails = new_emails.emails
        elif whitelist is not None:
            filtered_emails = [email_msg for email_msg in new_emails.emails if email_msg.sender.email in whitelist]
        else:  # only blacklist is not None
            filtered_emails = [email_msg for email_msg in new_emails.emails if email_msg.sender.email not in blacklist]

        if len(filtered_emails) != 0:
            fildered_email_ids = [email_msg.message_id for email_msg in filtered_emails]
            # stored_ids = kbm.process_new_emails(
            #     email_provider=email_profile,
            #     email_ids=fildered_email_ids,
            #     collection=collection
            # )
            # logger.info(f"Stored {len(stored_ids)} email chunks in knowledge base")
            return filtered_emails
        else:
            logger.info("No new emails found")
            return []
    except Exception as e:
        logger.error(f"Error checking new emails: {e}")
        raise e


def get_answer_for_email(
    email_profile: EmailProvider,
    kbm: KnowledgeBaseManager,
    email_assistant_config: Dict,
    email_message: EmailMessageModel,
    collection: str = "Email",
) -> str:
    """ Answer an email using the email assistant config.
    """
    try:

        # Check if email_assistant_config contains the sentder email
        if email_assistant_config["answer_patterns"].get(email_message.sender.email, None) is not None:
            answer_pattern = email_assistant_config["answer_patterns"][email_message.sender.email]["answer_pattern"]
        else:  # use the default answer pattern
            answer_pattern = "Hello {sender.email}, I am the email assistant. I have found the following information for your question: {context_results}"
        # search the knowledge base for the email message
        email_body = EmailPreprocessor().clean_email_body(email_message)
        context_results = kbm.search(email_body, collection=collection, strategy=SearchStrategy.HYBRID, top_k=3)

        if len(context_results.results) == 0:
            logger.info("No relevant context found for the email message, ID: {}, Subject: {}".format(email_message.message_id, email_message.subject))
            return None
        else:
            # Check the confidence score of the context results
            context_result_confident = ""
            for context_result in context_results.results:
                if context_result.similarity_score > 0.5:
                    context_result_confident += context_result.content + "\n"
            # find the answer pattern for the email message
            if context_result_confident != "":
                return answer_pattern.format(sender=email_message.sender.email, context_results=context_result_confident)
            else:
                logger.info("No answer pattern found for the email message, ID: {}, Subject: {}".format(email_message.message_id, email_message.subject))
            return None
    except Exception as e:
        logger.error(f"Error answering email: {e}")
        raise e


def email_assistant_workflow():
    """Email assistant workflow."""
    try:
        email_profile = initialize_email_profile()
        kbm = initialize_knowledge_base_manager()
        # Check if the collection exists
        collections = kbm.list_collections()
        email_assistant_config = load_email_assistant_config("email_assistant_config.json")
        if "Email" not in collections:
            email_database_creation(email_profile, kbm, whitelist=email_assistant_config["whitelist"])
            kbm.process_document("latex_documents/vahid.tex", collection="Email")
            kbm.process_document("latex_documents/mohamed.tex", collection="Email")

        while True:
            logger.info("Checking for new emails at {time}".format(time=time.strftime("%Y-%m-%d %H:%M:%S")))
            new_emails = check_new_emails(email_profile, kbm, collection="Email", limit=5, whitelist=email_assistant_config["whitelist"], blacklist=email_assistant_config["blacklist"])
            for email_message in new_emails:
                answer = get_answer_for_email(email_profile, kbm, email_assistant_config, email_message, collection="Email")
                logger.info(f"Answer for email: {email_message.message_id} is prepared, sender: {email_message.sender}, subject: {email_message.subject}, answer: {answer}")
                if answer is not None:
                    if email_assistant_config["answer_patterns"].get(email_message.sender.email, None) is not None and email_assistant_config["answer_patterns"][email_message.sender.email]["answer_type"] == "draft":
                        draft = draft_answer_for_email(email_profile, email_message, answer)
                        logger.info(f"Drafted answer for email: {email_message.message_id}, draft ID: {draft.draft_id}")
                    else:
                        send_answer_to_email(email_profile, email_message, answer)
                        logger.info(f"Sent answer to email: {email_message.message_id}")
            # wait for 2 minutes, but allow quitting with 'q'
            if wait_with_quit(120):
                logger.info("Quit requested by user. Exiting.")
                break
            continue
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e
    finally:
        email_profile.disconnect()
        kbm.close()
        logger.info("Disconnected from email servers")


def check_data_base_status():
    """Check the status of the data base."""
    try:
        kbm = initialize_knowledge_base_manager()
        collection_stats = kbm.get_collection_stats(collection="Email")
        # logger.info(f"Collection stats: {collection_stats}")

        search_results = kbm.search("Vahid", collection="Email", top_k=3)
        logger.info(f"Got {len(search_results.results)} results:")
        for i, result in enumerate(search_results.results, 1):
            logger.info(f"{i}. Result content: {result.get('content', '')}")
            logger.info(f"{i}. Result similarity score: {result.get('similarity_score', 0.0)}")
            logger.info(f"{i}. Result metadata: {result.get('metadata', '')}")
            logger.info(f"{i}. Result score: {result.get('score', 0.0)}")
            logger.info(f"{i}. Result score_detail: {result.get('score_detail', '')}")
            logger.info(f"{i}. Result score_detail_detail: {result.get('score_detail_detail', '')}")
            logger.info(f"{i}. Result score_detail_detail_detail: {result.get('score_detail_detail_detail', '')}")
            logger.info("--------------------------------")

    except Exception as e:
        logger.error(f"Error checking data base status: {e}")
        raise e
    finally:
        kbm.close()
        logger.info("Disconnected from data base")


def main():
    """Main function."""
    try:
        email_assistant_workflow()
        # check_data_base_status()
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e

if __name__ == "__main__":
    main()
