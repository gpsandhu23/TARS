from TARS.email_module.oauth_setup import setup_oauth

def main():
    print("Main before setup_oauth()")
    service = setup_oauth()
    print("Main after setup_oauth()")

if __name__ == "__main__":
    main()