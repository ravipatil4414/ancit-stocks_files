import boto3

def test_s3_access(s3_bucket_name):
    try:
        # Create a boto3 client for S3
        s3 = boto3.client('s3')

        # List objects in the specified S3 bucket
        response = s3.list_objects(Bucket=s3_bucket_name)

        # If no exception is raised, S3 access is successful
        print("S3 access successful")

    except Exception as e:
        # If an exception is raised, print the error message
        print(f"S3 access error: {e}")

if __name__ == "__main__":
    # Replace 'your_bucket_name' with the name of your S3 bucket
    test_s3_access('my-trading-data-bucket')

