import traceback
import logging
import boto3

from langchain.docstore.document import Document

from config.config import Configuration as config

logger = logging.getLogger(__file__)

class S3BucketFileUploadExtract:
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.auth_config = config.get_auth_config_aws()
    

    # Extract file from S3 Bucket
    def upload_file_to_s3(self):
        print("Inside upload_file_to_s3")
        try:
            key_flag = False
            aws_access_key_id_env = self.auth_config['aws_access_key_id']
            aws_secret_access_key_env = self.auth_config['aws_secret_access_key']
            aws_session_token_env = self.auth_config['aws_session_token']
            bucket_name_env = self.auth_config['s3_bucket_name_parse']
            
            client = boto3.client('s3', 
                                aws_access_key_id=aws_access_key_id_env, 
                                aws_secret_access_key=aws_secret_access_key_env, 
                                aws_session_token=aws_session_token_env)
            
            bucket_name = bucket_name_env
            
            file_name = self.file_path.split('/')[-1]
            result = client.list_objects(Bucket=bucket_name, Prefix='input_documents/')
            file_keys = []
            for file_s3_metadata in result['Contents']:
                file_keys.append(file_s3_metadata['Key'])
                
            for key in file_keys: 
                if file_name in key:
                    key_flag = True
                    break
            
            if key_flag == False:
                client.upload_file(self.file_path, bucket_name, 'input_documents/{}'.format(file_name))

        except Exception as e:
            print("Error is in function upload_file_to_s3. Error is {}".format(e))
            print(traceback.format_exc()) 
        return
    
    def extract_filename_from_s3(self):
        print("Inside extract_filename_from_s3")
        file_name = self.file_path.split('/')[-1]
        file = ''
        
        try:
            aws_access_key_id_env = self.auth_config['aws_access_key_id']
            aws_secret_access_key_env = self.auth_config['aws_secret_access_key']
            aws_session_token_env = self.auth_config['aws_session_token']
            bucket_name_env = self.auth_config['s3_bucket_name_parse']
            
            client = boto3.client('s3', 
                                aws_access_key_id=aws_access_key_id_env, 
                                aws_secret_access_key=aws_secret_access_key_env, 
                                aws_session_token=aws_session_token_env)
            
            bucket_name = bucket_name_env

            result = client.list_objects(Bucket=bucket_name, Prefix='input_documents/')
            for files in result['Contents']:
                file = files['Key']
                if file_name in file:
                    break
            
        except Exception as e:
            print("Error is in function extract_filename_from_s3. Error is {}".format(e))
            print(traceback.format_exc()) 
        return file

class AsyncAWSTextractDocumentAnalysis:
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.auth_config = config.get_auth_config_aws()
        
    # Collecting Required Bounding Box Data and Metadata and Getting Entire Document Text
    def extracting_required_metadata(collection_responses):
        print("Inside extracting_required_metadata")
        layout_analysis = {}
        
        try:
            all_blocks = []
            page_numbers = []
            layout_text = ''
            
            for response in collection_responses:
                blocks = response['Blocks']
                for block in blocks:
                    page_numbers.append(block['Page'])
                    all_blocks.append(block)

            page_numbers = list(set(page_numbers))
            for page in page_numbers:
                layout_analysis['page_{}'.format(page)] = {}   
                
            i = 0        
            for block in all_blocks:
                layout_text = ''
                if 'LAYOUT' in block['BlockType'] and block['BlockType'] != 'LAYOUT_LIST':
                    page = block['Page']
                    if 'Relationships' in block:
                        ids = block['Relationships'][0]['Ids']
                        for nested_block in all_blocks:
                            if nested_block['Id'] in ids:
                                if nested_block['BlockType'] == 'LINE':
                                    layout_text = layout_text + nested_block['Text'] + ' '
                                
                
                if block['BlockType'] == 'LAYOUT_LIST':
                    page = block['Page']
                    
                    if 'Relationships' in block:
                            ids = block['Relationships'][0]['Ids']
                            for nested_block in blocks:
                                if nested_block['Id'] in ids:
                                    text_ids = nested_block['Relationships'][0]['Ids']
                                    
                                    for nested_block_2 in blocks:
                                        if nested_block_2['Id'] in text_ids:
                                            if nested_block_2['BlockType'] == 'LINE':
                                                layout_text = layout_text + nested_block_2['Text'] + ' \n'
                    
                                                
                if 'LAYOUT' in block['BlockType']: 
                    
                    layout_analysis['page_{}'.format(page)]['section_{}'.format(i)] = {}
                    layout_analysis['page_{}'.format(page)]['section_{}'.format(i)]['layout_type'] = block['BlockType']
                    layout_analysis['page_{}'.format(page)]['section_{}'.format(i)]['text'] = layout_text
                    layout_analysis['page_{}'.format(page)]['section_{}'.format(i)]['page'] = block['Page']
                    # layout_analysis['page_{}'.format(page)]['section_{}'.format(i)]['geometry'] = block['Geometry']
                    

                i += 1
        
        except Exception as e:
            print("Error is in function extracting_required_metadata. Error is {}".format(e))
            print(traceback.format_exc())  
                        
        return layout_analysis

    def langchain_document_object(layout_analysis):
        print("Inside langchain_document_object")
        document_object_lists = []
        for page in layout_analysis:
            for section in layout_analysis[page]:
                text_output = layout_analysis[page][section]['text']
                metadata_output = {
                    "page": layout_analysis[page][section]['page'],
                    "layout_type": layout_analysis[page][section]['layout_type']
                }
                document_object_lists.append(Document(page_content = text_output, metadata = metadata_output))            
                
        return document_object_lists
    
    # Parsing Provided Document using AWS Textract
    def extract_text_from_pdf_async_doc_analysis(self):
        print("Inside extract_text_from_pdf_async_doc_analysis")
        document_bounding_box_info = {}
        document_object_list_info = []
        s3_bucket_obj = S3BucketFileUploadExtract(self.file_path)
        try:
            # Replace 'your-region' and 'your-bucket-name' with your AWS region and S3 bucket name
            aws_access_key_id = self.auth_config['aws_access_key_id']
            aws_secret_access_key = self.auth_config['aws_secret_access_key']
            aws_session_token = self.auth_config['aws_session_token']
            region = self.auth_config['aws_region']
            bucket_name = self.auth_config['s3_bucket_name_parse']
            queue_url = self.auth_config['sqs_url_async_textract']
            sns_topic_arn = self.auth_config['sns_topic_arn_async_textract']
            role_arn = self.auth_config['iam_role']

            # Upload file to S3 Bucket
            s3_bucket_obj.upload_file_to_s3()
            
            # Extract file name from S3 Bucket
            file_name = s3_bucket_obj.extract_filename_from_s3()
            
            # Create a Textract Client 
            textract_client = boto3.client('textract', 
                                        region_name=region,
                                        aws_access_key_id=aws_access_key_id, 
                                        aws_secret_access_key=aws_secret_access_key, 
                                        aws_session_token=aws_session_token
                                    )
            # Start the Textract Job (Start Document Analysis - Is Asynchronous with a size limit of 500MB)
            textract_job = textract_client.start_document_analysis(
                DocumentLocation = {
                    'S3Object':{
                        'Bucket': bucket_name,
                        'Name': file_name         
                    }
                },
                FeatureTypes = [
                    'LAYOUT'
                ],
                NotificationChannel = {
                    'SNSTopicArn': sns_topic_arn,
                    'RoleArn': role_arn
                }
            )

            # Receiving notification from the subsrciption between SNS and SQS
            sqs_body_text = ''
            sqs_client = boto3.client('sqs', 
                                        region_name=region,
                                        aws_access_key_id=aws_access_key_id, 
                                        aws_secret_access_key=aws_secret_access_key, 
                                        aws_session_token=aws_session_token
                                    )
            while 'SUCCEEDED' not in sqs_body_text and file_name.split("/")[-1].split()[0] not in sqs_body_text:
                sqs_response = sqs_client.receive_message(
                    QueueUrl = queue_url,
                    AttributeNames = [
                        'All'
                    ],
                    MessageAttributeNames = [
                        'string',
                    ],
                    MaxNumberOfMessages = 5,
                    VisibilityTimeout = 10,
                    WaitTimeSeconds = 20,
                    ReceiveRequestAttemptId = 'string'
                )
                if 'Messages' not in sqs_response:
                    continue
                    
                sqs_body_text = sqs_response['Messages'][0]['Body'] # This text includes required JobId and Status of StartDocumentAnalysis

            job_id = sqs_body_text.split('\\"JobId\\":\\"',1)[1].split('\\')[0]
            receipt_handle = sqs_response['Messages'][0]['ReceiptHandle']

            # Delete received message from queue
            sqs_client.delete_message(
                QueueUrl = queue_url,
                ReceiptHandle = receipt_handle
            )
            textract_response = textract_client.get_document_analysis(JobId=job_id, MaxResults=1000)
            collection_textract_responses = [textract_response]

            # To get next token i.e. position from where GetDocumentAnalysis should continue to get remaining document
            next_token = None
            if 'NextToken' in textract_response:
                next_token = textract_response['NextToken']
            while next_token:
                
                textract_response = textract_client.get_document_analysis(JobId=job_id, NextToken=next_token, MaxResults=1000)
                collection_textract_responses.extend([textract_response])

                
                if 'NextToken' in textract_response:
                    next_token = textract_response['NextToken']
                    
                else:
                    collection_textract_responses.extend([textract_response])
                    break
            
            document_bounding_box_info = AsyncAWSTextractDocumentAnalysis.extracting_required_metadata(collection_textract_responses)
            document_object_list_info = AsyncAWSTextractDocumentAnalysis.langchain_document_object(document_bounding_box_info)

        except Exception as e:
            print(traceback.format_exc())
            print("Error in function - extract_text_from_pdf_async_doc_analysis. Error is {}".format(e))
            
        return document_object_list_info

def main(file_path: str):
    
    async_aws_textract = AsyncAWSTextractDocumentAnalysis(file_path)
    document_object_langchain_format = async_aws_textract.extract_text_from_pdf_async_doc_analysis()
    return document_object_langchain_format

input_file_path = 'rinvqq.pdf'
main(input_file_path)
