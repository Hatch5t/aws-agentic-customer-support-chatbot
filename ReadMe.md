# Customer Support Chatbot with Amazon Bedrock

An end-to-end customer support chatbot built using **Amazon Bedrock Flows**, **Amazon Bedrock AgentCore**, **Amazon Bedrock AgentCore Gateway**, **AWS Lambda**, and **Amazon DynamoDB**.

The application is designed to receive a customer's message, determine the type of request, and route it to the appropriate support workflow. The system combines deterministic flow-based routing with an agentic workflow for collecting and persisting bug reports.

---

## Overview

The chatbot supports three primary request categories:

- **Bug Reports** — customers reporting an issue are routed to an AgentCore-managed agent that collects the information required to create a bug report.
- **Platform Questions** — questions covered by the application's FAQ are answered using the available FAQ content.
- **Other Requests** — requests that are outside the supported FAQ or bug-report workflows are directed to human customer support.

The architecture separates **classification and routing** from the specialized handling of each request. This allows the Bedrock Flow to make the routing decision while the downstream components focus on the work required for each category.

---

## Architecture

The high-level architecture is:

```text
                              CUSTOMER
                                 |
                                 v
                    +--------------------------+
                    |    Amazon Bedrock Flow   |
                    |                          |
                    |  Request Classification  |
                    +------------+-------------+
                                 |
                +----------------+----------------+
                |                |                |
                v                v                v
        +---------------+ +---------------+ +---------------+
        |  BUG REPORT   | |   PLATFORM    | |     OTHER     |
        |     PATH      | |   QUESTION    | |    REQUEST    |
        +-------+-------+ +-------+-------+ +-------+-------+
                |                 |                 |
                v                 v                 v
        +---------------+ +---------------+ +---------------+
        |   AgentCore   | |      FAQ      | |    Human      |
        |     Agent     | |    Content    | |   Support     |
        |    Harness    | |               | |               |
        +-------+-------+ +---------------+ +---------------+
                |
                v
        +-------------------+
        | create_bug_report |
        |       Tool        |
        +---------+---------+
                  |
                  v
        +-------------------+
        | AgentCore Gateway |
        +---------+---------+
                  |
                  v
             +---------+
             | Lambda  |
             +----+----+
                  |
                  v
             +---------+
             | DynamoDB|
             +---------+
```

---

# Request Classification and Routing

The first stage of the application is the Amazon Bedrock Flow.

The Flow receives the customer's message and uses a classifier to determine which category the request belongs to.

The classifier produces a routing value that is used by conditional nodes in the Flow.

```text
Customer Message
       |
       v
Request Classifier
       |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
  Bug Report       Platform Question      Other Request
       |                   |                   |
       v                   v                   v
 Bug Report Path      FAQ Path          Support Path
```

This separation ensures that each category follows a distinct workflow rather than relying on a single response strategy for every customer message.

---

# Bug Report Workflow

Bug reports use the AgentCore-managed harness.

The bug-report behavior is defined in the system prompt. The agent is responsible for collecting the information necessary to create a useful ticket before invoking the backend tool.

The conversation follows the general pattern:

```text
Customer reports a problem
          |
          v
Agent acknowledges the issue
          |
          v
Collect bug description
          |
          v
Collect steps to reproduce
          |
          v
Collect environment information
          |
          v
create_bug_report tool
          |
          v
AgentCore Gateway
          |
          v
AWS Lambda
          |
          v
Amazon DynamoDB
```

The tool is intended to be invoked after the required information has been collected.

This allows the chatbot to turn an unstructured customer conversation into a persistent bug-report record.

## AgentCore Tool Integration

The backend tool is exposed to the AgentCore harness through the AgentCore Gateway.

```text
AgentCore Harness
       |
       | Tool invocation
       v
AgentCore Gateway
       |
       v
AWS Lambda
       |
       v
DynamoDB
```

The Lambda function performs the backend operation required to persist the bug report.

---

# Platform Question Workflow

Platform questions follow a separate FAQ-based path.

```text
Customer Question
       |
       v
Platform Question Route
       |
       v
FAQ Content
       |
       +-------------------------+
       |                         |
       v                         v
Question Covered          Question Not Covered
       |                         |
       v                         v
Relevant FAQ Answer        Human Support
```

When the customer's question is covered by the FAQ, the chatbot provides a relevant answer based on the available FAQ information.

For questions that are not covered, the application can direct the customer to human support instead of fabricating information that is not present in the FAQ.

The FAQ content is stored in:

```text
online_shop_faq.md
```

---

# Other Customer Requests

Requests that do not belong to the supported bug-report or platform-question categories follow the other-request path.

```text
Customer Request
       |
       v
Other Request Route
       |
       v
Human Customer Support
       |
       v
1-800-555-0199
```

This provides a clear fallback for requests that cannot be handled by the application's specialized workflows.

---

# Project Structure

The repository is organized around the application implementation, infrastructure, testing, and evaluation components.

```text
project/
│
├── README.md
│
├── chat.py
├── system_prompt.txt
│
├── create_harness.py
├── setup_gateway.py
├── create_bug_report.py
├── cleanup_agentcore.py
│
├── generate-eval-dataset.py
│
├── agentcore_config.json
│
├── cloudformation-tool.yaml
├── cloudformation-testing.yaml
│
├── harness-tests-template.json
├── harness-tests.json
│
├── online_shop_faq.md
├── output_eval_dataset.jsonl
│
└── requirements.txt
```

### Application

| File | Description |
|---|---|
| `chat.py` | Application entry point used to interact with the customer-support chatbot. |
| `system_prompt.txt` | Defines the chatbot's behavior, including the bug-report workflow and response instructions. |
| `online_shop_faq.md` | FAQ content used for platform-question responses. |

### AgentCore and Tooling

| File | Description |
|---|---|
| `create_harness.py` | Creates/configures the AgentCore harness used by the bug-report workflow. |
| `setup_gateway.py` | Configures the AgentCore Gateway and its integration with the backend tool. |
| `create_bug_report.py` | Defines the bug-report tool used to persist ticket information. |
| `agentcore_config.json` | Stores the AgentCore resource configuration and identifiers required by the project. |
| `cleanup_agentcore.py` | Removes the AgentCore resources created for the project. |

### Infrastructure

| File | Description |
|---|---|
| `cloudformation-tool.yaml` | Defines the AWS infrastructure required by the bug-report tool workflow. |
| `cloudformation-testing.yaml` | Defines the infrastructure used for the automated testing and Bedrock Evaluation workflow. |

### Testing and Evaluation

| File | Description |
|---|---|
| `harness-tests-template.json` | Template for defining automated test cases. |
| `harness-tests.json` | Test cases used to exercise the chatbot's different routes. |
| `generate-eval-dataset.py` | Executes the test prompts against the harness and generates the evaluation dataset. |
| `output_eval_dataset.jsonl` | JSONL dataset containing prompts, reference responses, and generated chatbot responses. |

### Dependencies

```text
requirements.txt
```

contains the Python dependencies required to run the project scripts.

---

# Automated Testing and Evaluation

The project includes an automated testing workflow to verify the chatbot's behavior across its different request paths.

The complete workflow is:

```text
                Test Prompts
                     |
                     v
             harness-tests.json
                     |
                     v
        generate-eval-dataset.py
                     |
                     v
             AgentCore Harness
                     |
                     v
            Chatbot Responses
                     |
                     v
        output_eval_dataset.jsonl
                     |
                     v
                Amazon S3
                     |
                     v
        Amazon Bedrock Evaluations
                     |
                     v
              Amazon Nova Pro
             LLM-as-a-Judge
```

The evaluation dataset contains the original prompt, a reference description of the expected behavior, and the actual response generated by the chatbot.

---

# Test Case Format

Test cases are defined in `harness-tests.json`.

The structure is:

```json
{
  "tests": [
    {
      "id": "unique-test-id",
      "prompt": "customer-message",
      "expected": "description-of-expected-response"
    }
  ]
}
```

### Test ID

Each test has a unique identifier used to identify the test during execution.

### Prompt

The prompt represents the customer's message that is sent to the chatbot.

### Expected Response

The `expected` field describes what a successful response should accomplish.

It is used as the reference for evaluation rather than requiring an exact text match.

---

# Evaluation with Amazon Bedrock

The project uses **Amazon Bedrock Evaluations** with the **LLM-as-a-Judge** method.

The chatbot responses are generated first and stored in the JSONL dataset. The evaluation service then assesses those responses against the supplied reference responses.

```text
             Generated Responses
                     |
                     v
          output_eval_dataset.jsonl
                     |
                     v
                     S3
                     |
                     v
       Amazon Bedrock Evaluations
                     |
                     v
              Amazon Nova Pro
                     |
                     v
             Evaluation Scores
```

The evaluation was configured with:

- **Evaluation type:** Automatic — LLM as a judge
- **Inference source:** `my-support-chatbot`
- **Evaluator:** Amazon Nova Pro
- **Task type:** General

The evaluation considered response quality and responsible-AI behavior.

---

# Evaluation Results

The completed evaluation produced the following results:

| Metric | Score |
|---|---:|
| Correctness | **0.83** |
| Following instructions | **0.50** |
| Harmfulness | **0.00** |

The correctness score indicates that the chatbot's responses were generally aligned with the expected behavior represented by the evaluation references.

The following-instructions score indicates that there is room to improve how consistently the chatbot follows the desired response behavior.

The harmfulness score of `0.00` indicates that the evaluated responses did not exhibit the harmful-content behavior measured by this metric.

---

# AWS Services

The project brings together several AWS services, each with a specific responsibility.

### Amazon Bedrock

Provides the foundation for the Flow, model interactions, and evaluation capabilities.

### Amazon Bedrock Flows

Handles request classification and routing.

### Amazon Bedrock AgentCore

Provides the managed harness used by the bug-report workflow.

### AgentCore Gateway

Provides the connection between the AgentCore agent and the backend tool.

### AWS Lambda

Executes the backend bug-report operation.

### Amazon DynamoDB

Provides persistent storage for created bug reports.

### Amazon S3

Stores the evaluation dataset and evaluation-related artifacts.

### Amazon Bedrock Evaluations

Provides automated evaluation of the chatbot responses.

### Amazon Nova Pro

Acts as the evaluator model for the LLM-as-a-Judge workflow.

---

# Running the Project

The testing/evaluation scripts require Python and `boto3`.

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Verify the AWS SDK:

```bash
python -c "import boto3; print(boto3.__version__)"
```

The automated evaluation dataset can be generated with:

```bash
python generate-eval-dataset.py --tests-json harness-tests.json
```

This produces:

```text
output_eval_dataset.jsonl
```

---

# Infrastructure and Evaluation Data

The evaluation infrastructure is defined using CloudFormation.

The testing stack can be deployed with:

```bash
aws cloudformation deploy \
  --template-file cloudformation-testing.yaml \
  --stack-name bug-report-testing-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

The stack outputs provide the S3 bucket and IAM role required for the evaluation workflow.

The generated evaluation dataset can then be uploaded to S3:

```bash
aws s3 cp output_eval_dataset.jsonl \
  s3://<EvalDatasetBucketName>/output_eval_dataset.jsonl \
  --region us-east-1
```

---

# Design Rationale

The architecture intentionally separates the responsibilities of classification, request handling, tool execution, and persistence.

### Flow-based routing

The Bedrock Flow provides a clear entry point and makes the routing behavior explicit.

### Agentic bug reporting

Bug reports require information gathering rather than a single static answer. AgentCore allows the chatbot to conduct this interaction and invoke a tool when sufficient information has been collected.

### Serverless backend

Lambda provides the backend execution layer, while DynamoDB provides persistent storage without requiring a continuously running server.

### Automated evaluation

The testing workflow makes it possible to repeatedly exercise the chatbot against a defined set of customer messages and evaluate the resulting responses using an LLM-as-a-Judge.

---

# Security

AWS credentials, secret keys, passwords, tokens, and other sensitive configuration should never be committed to this repository.

Do not commit:

```text
.env
AWS access keys
AWS secret keys
Passwords
Private tokens
Credential files
```

AWS permissions should be provided through the appropriate IAM roles or local AWS credential configuration.

---

# Cleanup

AWS resources created for the project should be removed when they are no longer required.

AgentCore resources can be removed using:

```bash
python cleanup_agentcore.py
```

The evaluation S3 bucket should be emptied before deleting the CloudFormation stack:

```bash
aws s3 rm s3://<EvalDatasetBucketName> \
  --recursive \
  --region us-east-1
```

The testing stack can then be deleted:

```bash
aws cloudformation delete-stack \
  --stack-name bug-report-testing-stack \
  --region us-east-1
```

The tool stack can be deleted with:

```bash
aws cloudformation delete-stack \
  --stack-name bug-report-tool-stack \
  --region us-east-1
```

---

# Summary

This project demonstrates a complete agentic customer-support architecture on AWS.

A customer message enters an **Amazon Bedrock Flow**, where it is classified and routed to the appropriate workflow. Bug reports are handled by an **AgentCore-managed agent**, which collects the required information and uses an **AgentCore Gateway** to invoke an **AWS Lambda** tool that persists the report in **Amazon DynamoDB**. Platform questions are handled using the application's FAQ, while unsupported requests are directed to human support.

The project also includes an automated testing and evaluation pipeline. Test prompts are executed against the AgentCore harness, the resulting responses are stored as a JSONL dataset, and **Amazon Bedrock Evaluations** uses **Amazon Nova Pro as an LLM-as-a-Judge** to assess response quality.

The resulting architecture provides a clear separation between routing, agentic interaction, backend tool execution, persistence, testing, and evaluation.
