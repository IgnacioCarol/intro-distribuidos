from src.upload.upload_cli import UploadCLI


def main():
    args = UploadCLI().parse_args()

    print(
        "If you read this line it means that you have provided "
        "all the parameters which are:"
    )
    print(args)


main()
