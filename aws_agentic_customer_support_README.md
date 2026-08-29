# AWS Agentic Customer Support Chatbot

An agentic customer support application built with **Amazon Bedrock Flows**, **Amazon Bedrock AgentCore**, **AWS Lambda**, **Amazon DynamoDB**, and **Amazon Bedrock Evaluations**.

The application classifies incoming customer messages and routes them to the appropriate support path:

- **Bug Report** — collects the required information and creates a persistent bug report.
- **Platform Question** — answers questions covered by the embedded FAQ.
- **Other Request** — directs the customer to human support.

The project also includes an automated testing and evaluation workflow using an **LLM-as-a-Judge** evaluation with **Amazon Nova Pro**.

---

## 1. Project Overview

The goal of this project is to build an end-to-end customer support chatbot that can distinguish between different types of customer requests and respond appropriately.

The system combines deterministic routing with an agentic bug-report workflow.

### Main capabilities

1. Classify incoming customer messages.
2. Route messages to distinct paths.
3. Handle bug reports through an AgentCore-managed harness.
4. Collect bug information conversationally.
5. Persist completed bug reports through a Lambda tool into DynamoDB.
6. Answer supported platform questions using FAQ content.
7. Route unsupported/general support requests to a human support phone number.
8. Test all three routes automatically.
9. Generate an evaluation dataset in JSONL format.
10. Evaluate response quality using Amazon Bedrock Evaluations.

---

# 2. System Architecture

The overall request flow is:

```text
                         Customer
                            |
                            v
                 +----------------------+
                 |  Amazon Bedrock Flow |
                 |  Request Classifier  |
                 +----------+-----------+
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
       +------------+ +-------------+ +-------------+
       | Bug Report | |  Platform   | |  Anything   |
       |    Path    | |  Question   | |    Else     |
       +------+-----+ +------+------+ +------+------+
              |              |               |
              v              v               v
       +-------------+ +-------------+ +-------------+
       |  AgentCore  | | FAQ-Grounded| |    Human    |
       |    Agent    | |   Response  | |   Support   |
       +------+------+
              |
              v
       +------------------+
       | create_bug_report|
       |      Tool        |
       +--------+---------+
                |
                v
          +-----------+
          |  Lambda   |
          +-----+-----+
                |
                v
          +-----------+
          | DynamoDB  |
          | Bug Reports|
          +-----------+
```

## Component responsibilities

### Amazon Bedrock Flow

The Flow receives the customer's message and determines which support category it belongs to.

The classifier produces an unambiguous category that drives routing.

### Bug Report Path

The bug-report path is defined in the system prompt rather than as a separate agent resource.

The AgentCore-managed harness uses the bug-report tool to persist the completed ticket.

The assistant collects:

- Bug description
- Steps to reproduce
- Environment information

The tool is called only after the required information has been collected.

### Platform Question Path

The platform-question route uses the embedded FAQ content to answer questions covered by the FAQ.

Questions outside the FAQ are directed to support rather than answered with unsupported information.

### Other Request Path

Requests that do not belong to the supported platform-question or bug-report categories are directed to human support.

Example support number:

```text
1-800-555-0199
```

---

# 3. Repository Structure

Recommended repository structure:

```text
aws-agentic-customer-support/
|
├── README.md
|
├── src/
│   ├── chat.py
│   ├── system_prompt.txt
│   ├── create_harness.py
│   ├── setup_gateway.py
│   ├── create_bug_report.py
│   ├── generate-eval-dataset.py
│   └── cleanup_agentcore.py
|
├── tests/
│   ├── harness-tests.json
│   └── harness-tests-template.json
|
├── faq/
│   └── online_shop_faq.md
|
├── infrastructure/
│   ├── cloudformation-tool.yaml
│   ├── cloudformation-testing.yaml
│   └── agentcore_config.json
|
├── evaluation/
│   └── output_eval_dataset.jsonl
|
├── evidence/
│   ├── 01-flow-overview.png
│   ├── 02-classifier-configuration.png
│   ├── 03-condition-routing.png
│   ├── 04-bug-report-conversation.png
│   ├── 05-bug-report-tool-call.png
│   ├── 06-dynamodb-record.png
│   ├── 07-faq-response.png
│   ├── 08-faq-gap-response.png
│   ├── 09-other-request-response.png
│   ├── 10-prompt-injection.png
│   ├── 11-automated-tests.png
│   ├── 12-evaluation-dataset.png
│   ├── 13-bedrock-evaluation.png
│   └── 14-evaluation-results.png
|
└── requirements.txt
```

Adjust filenames to match the actual files in the final repository.

---

# 4. Classification and Routing

The Flow classifies incoming customer messages into distinct categories.

The classifier must produce a consistent and unambiguous result so that the message can be routed correctly.

The three major routes are:

```text
Customer Message
       |
       v
Request Classification
       |
       +------------------+------------------+
       |                  |                  |
       v                  v                  v
  Bug Report       Platform Question    Anything Else
```

Each route terminates in its appropriate output behavior.

---

# 5. Bug Report Workflow

The bug-report route is handled by the AgentCore-managed harness.

The system prompt defines the bug-report behavior.

The assistant should collect the necessary information before invoking the tool:

```text
Customer
   |
   v
Describe the problem
   |
   v
Collect reproduction steps
   |
   v
Collect environment information
   |
   v
create_bug_report
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

A completed bug report creates a record in the bug-report DynamoDB table.

The conversation should demonstrate that the assistant asks follow-up questions rather than immediately creating an incomplete ticket.

---

# 6. Platform Question Workflow

Platform questions are handled using the embedded FAQ.

```text
Customer Question
       |
       v
Platform Question Route
       |
       v
FAQ Content
       |
       +----------------------+
       |                      |
       v                      v
Question Covered        Question Not Covered
       |                      |
       v                      v
Relevant FAQ Answer      Human Support
```

The chatbot should provide a relevant answer when the question is covered by the FAQ.

If the answer is not covered by the FAQ, the application should direct the user to the support phone number rather than inventing an answer.

---

# 7. Other Request Workflow

Requests that do not belong to the bug-report or supported platform-question routes are sent to the human-support path.

```text
Other Customer Request
          |
          v
    Other Request Path
          |
          v
 Human Support Number
    1-800-555-0199
```

---

# 8. Automated Testing

The project includes an automated testing workflow.

The testing process is:

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
```

Each test case runs as a single turn in a fresh session.

Therefore, test cases must not depend on previous conversation turns.

---

## Test Case Structure

The test file uses the following structure:

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

### `id`

A unique identifier for the test case.

Example:

```text
t1_bug_report
```

### `prompt`

The customer message sent to the harness.

Test prompts should be realistic and clearly belong to one of the supported categories.

### `expected`

A description of what a good response should contain.

It does not need to be an exact response. It acts as the reference response for the LLM-as-a-Judge evaluation.

---

# 9. Required Test Coverage

The automated test suite should contain at least:

1. One test for the **Bug Report** path.
2. One test for the **Platform Question** path.
3. One test for the **Other Request** path.

Additional edge-case tests are recommended.

Useful additional tests include:

- Ambiguous customer messages
- Very short messages
- Unsupported FAQ questions
- Prompt injection attempts
- Requests that could potentially be confused between categories

---

# 10. Python Testing Environment

The evaluation dataset generator uses `boto3` to call the Bedrock AgentCore API.

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

Verify `boto3`:

```bash
python -c "import boto3; print(boto3.__version__)"
```

The course instructions specify that the AgentCore APIs require a sufficiently recent `boto3` version.

---

# 11. Generate the Evaluation Dataset

Run:

```bash
python generate-eval-dataset.py --tests-json harness-tests.json
```

The script invokes the harness once for each test prompt and writes the results to:

```text
output_eval_dataset.jsonl
```

Each line contains the information required by Bedrock Evaluations.

Example structure:

```json
{
  "prompt": "Your app crashes every time I try to upload a file...",
  "referenceResponse": "Acknowledges the issue and asks for steps to reproduce.",
  "modelResponses": [
    {
      "response": "I'm sorry to hear about the crash. Could you tell me...",
      "modelIdentifier": "my-support-chatbot"
    }
  ]
}
```

If a harness call fails, the response contains an error prefixed with:

```text
[HARNESS_ERROR]
```

Check the terminal output for the specific failure.

---

# 12. Testing Infrastructure

Before creating the Bedrock Evaluation job, deploy the testing infrastructure.

The testing stack is defined in:

```text
cloudformation-testing.yaml
```

Deploy it with:

```bash
aws cloudformation deploy \
  --template-file cloudformation-testing.yaml \
  --stack-name bug-report-testing-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Retrieve the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name bug-report-testing-stack \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region us-east-1
```

The important outputs are:

```text
EvalDatasetBucketName
BedrockEvalRoleArn
```

Keep these values available for the evaluation job.

---

# 13. Upload the Evaluation Dataset

Upload the generated JSONL file:

```bash
aws s3 cp output_eval_dataset.jsonl \
  s3://<EvalDatasetBucketName>/output_eval_dataset.jsonl \
  --region us-east-1
```

The resulting S3 URI is:

```text
s3://<EvalDatasetBucketName>/output_eval_dataset.jsonl
```

---

# 14. Amazon Bedrock Evaluation

The project uses **Bring Your Own Inference (BYOI)**.

The chatbot responses are already present in the JSONL dataset, so Bedrock Evaluations does not need to invoke the chatbot again.

Instead, the evaluator judges the supplied responses.

The evaluation uses:

```text
Evaluator:
Amazon Nova Pro
```

and evaluates response quality using an LLM-as-a-Judge approach.

---

# 15. Evaluation Job Configuration

The evaluation configuration follows this structure:

```text
Task type:
General

Dataset:
output_eval_dataset.jsonl

Metric:
BuiltIn.Correctness

Evaluator:
amazon.nova-pro-v1:0

Inference source:
my-support-chatbot
```

The `inferenceSourceIdentifier` must match the `modelIdentifier` in the JSONL dataset.

The default identifier generated by the evaluation script is:

```text
my-support-chatbot
```

---

# 16. Evaluation Results

The evaluation results should be reviewed for:

- Correctness
- Following instructions
- Harmfulness

The results page provides overall scores and per-record breakdowns.

Example evaluation results from the completed run:

```text
Correctness:          0.83
Following instructions: 0.50
Harmfulness:          0.00
```

These scores are normalized between 0 and 1 where applicable.

The correctness result of:

```text
0.83
```

indicates that the evaluated responses were generally correct, while the following-instructions score of:

```text
0.50
```

indicates there is room for improvement in adherence to the expected response behavior.

The harmfulness score was:

```text
0.00
```

The evaluation results should be included as submission evidence.

---

# 17. Evaluation Workflow Diagram

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
                       S3
                         |
                         v
              Bedrock Evaluations
                         |
                         v
                 Amazon Nova Pro
                 LLM-as-a-Judge
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
        Correctness  Instructions  Harmfulness
           0.83         0.50          0.00
```

---

# 18. Submission Evidence

The project rubric requires evidence for the major implementation areas.

Recommended evidence organization:

## Classification and Routing

Include screenshots showing:

- Full Flow diagram
- Classifier prompt/configuration
- Condition node expressions/routing

Suggested files:

```text
01-flow-overview.png
02-classifier-configuration.png
03-condition-routing.png
```

---

## Bug Report Path

Include:

- Submitted `system_prompt.txt`
- Bug-report conversation
- Follow-up questions collecting required information
- Tool call to `create_bug_report`
- DynamoDB record showing the created bug report

Suggested evidence:

```text
04-bug-report-conversation.png
05-bug-report-tool-call.png
06-dynamodb-record.png
```

---

## Platform Question and Other Request Paths

Include screenshots showing:

- FAQ-backed response for a covered question
- Response for an uncovered FAQ question
- Other-request response directing the customer to human support

Suggested evidence:

```text
07-faq-response.png
08-faq-gap-response.png
09-other-request-response.png
```

---

## Testing and Evaluation

Include:

- Automated test execution
- Generated JSONL evaluation dataset
- Bedrock Evaluation job
- Final evaluation results

Suggested evidence:

```text
11-automated-tests.png
12-evaluation-dataset.png
13-bedrock-evaluation.png
14-evaluation-results.png
```

If prompt-injection or other safety testing is included, also include:

```text
10-prompt-injection.png
```

---

# 19. Rubric Checklist

## Implement Classification and Routing

- [ ] Flow classifies incoming customer messages.
- [ ] Classifier output is consistent and unambiguous.
- [ ] Messages are routed to distinct paths.
- [ ] Each path has an appropriate output.
- [ ] Full Flow screenshot captured.
- [ ] Classifier configuration screenshot captured.
- [ ] Condition/routing screenshot captured.

---

## Implement Bug Report Path

- [ ] Bug-report path is defined in the system prompt.
- [ ] AgentCore harness invokes the Lambda tool through the Gateway.
- [ ] Assistant collects bug description.
- [ ] Assistant collects reproduction steps.
- [ ] Assistant collects environment information.
- [ ] Tool is called after the necessary information is collected.
- [ ] Bug report is persisted in DynamoDB.
- [ ] Bug-report conversation screenshot captured.
- [ ] Tool-call screenshot captured.
- [ ] DynamoDB record screenshot captured.

---

## Implement Platform Question and Other Request Paths

- [ ] Covered FAQ question receives a relevant answer.
- [ ] Unsupported FAQ question is directed to support.
- [ ] Other requests are directed to human support.
- [ ] FAQ prompt configuration screenshot captured.
- [ ] Covered-question response captured.
- [ ] Uncovered-question response captured.
- [ ] Other-request response captured.

---

## Testing and Evaluation

- [ ] `harness-tests.json` contains a bug-report test.
- [ ] `harness-tests.json` contains a platform-question test.
- [ ] `harness-tests.json` contains an other-request test.
- [ ] Test script runs successfully.
- [ ] `output_eval_dataset.jsonl` is generated.
- [ ] JSONL dataset is uploaded to S3.
- [ ] Bedrock Evaluation job is created.
- [ ] Evaluation uses an LLM-as-a-Judge.
- [ ] Evaluation results are available.
- [ ] Correctness score is reasonably high.
- [ ] Evaluation results screenshot captured.
- [ ] JSONL output included as evidence.
- [ ] Written evaluation observations included in the README or a separate report.

---

# 20. Suggested Evaluation Observations

The evaluation results should not simply be uploaded without explanation.

For the observed evaluation:

```text
Correctness: 0.83
Following instructions: 0.50
Harmfulness: 0.00
```

The main observation is that the chatbot demonstrates generally good correctness but has room for improvement in following the expected response behavior.

Potential improvements include:

- Making category definitions more explicit.
- Tightening the FAQ-only answering instruction.
- Making the bug-report collection checklist more explicit.
- Adding additional edge-case tests.
- Testing ambiguous requests.
- Testing prompt-injection attempts.
- Reviewing individual low-scoring records rather than relying only on the aggregate score.

---

# 21. Cleanup

After completing the project and capturing all required evidence, clean up the AWS resources to avoid unnecessary charges.

## Step 1: Delete AgentCore resources

Run:

```bash
python cleanup_agentcore.py
```

This removes the AgentCore resources defined in:

```text
agentcore_config.json
```

The cleanup removes the resources in the required order, including the harness, gateway target, and gateway.

---

## Step 2: Empty the evaluation S3 bucket

CloudFormation cannot delete a non-empty S3 bucket.

First empty the bucket:

```bash
aws s3 rm s3://<EvalDatasetBucketName> \
  --recursive \
  --region us-east-1
```

---

## Step 3: Delete the testing stack

```bash
aws cloudformation delete-stack \
  --stack-name bug-report-testing-stack \
  --region us-east-1
```

---

## Step 4: Delete the tool stack

```bash
aws cloudformation delete-stack \
  --stack-name bug-report-tool-stack \
  --region us-east-1
```

---

## Step 5: Optional local cleanup

If the virtual environment is no longer required:

```bash
rm -rf venv
```

Do not delete local project files until the final submission has been backed up.

---

# 22. Security

Do **not** commit any of the following to GitHub:

```text
AWS access keys
AWS secret keys
.env files
AWS credentials
Private tokens
Passwords
Private account information
```

Use IAM roles, AWS CLI configuration, environment variables, or other appropriate credential mechanisms.

Before pushing the repository, inspect the files for secrets.

---

# 23. Final Repository Checklist

Before submitting, verify that the repository contains:

```text
[ ] README.md
[ ] Source code
[ ] system_prompt.txt
[ ] Test JSON
[ ] Evaluation JSONL
[ ] CloudFormation templates
[ ] FAQ content
[ ] requirements.txt
[ ] Evidence screenshots
[ ] Architecture/flow diagrams
```

Also verify:

```text
[ ] No AWS credentials
[ ] No secret keys
[ ] No .env files containing secrets
[ ] No unnecessary generated files
[ ] All screenshots are readable
[ ] README explains the architecture
[ ] README explains testing
[ ] README explains evaluation
[ ] Evaluation score is documented
[ ] Cleanup completed after evidence was captured
```

---

# 24. Project Flow at a Glance

```text
                         +----------------+
                         |    Customer    |
                         +-------+--------+
                                 |
                                 v
                    +-------------------------+
                    |   Amazon Bedrock Flow   |
                    | Classification + Routing|
                    +-----------+-------------+
                                |
              +-----------------+-----------------+
              |                 |                 |
              v                 v                 v
       +-------------+   +-------------+   +-------------+
       | Bug Report  |   |  Platform   |   |    Other    |
       |    Route    |   |  Question   |   |   Request   |
       +------+------+   +------+------+   +------+------+
              |                 |                 |
              v                 v                 v
       +-------------+   +-------------+   +-------------+
       |  AgentCore  |   |     FAQ     |   |   Human     |
       |   Harness   |   |   Content   |   |   Support   |
       +------+------+   +------+------+   +-------------+
              |
              v
       +-------------+
       | Bug Report  |
       |    Tool     |
       +------+------+
              |
              v
          +-------+
          | Lambda|
          +---+---+
              |
              v
         +----------+
         | DynamoDB |
         +----------+


Testing / Evaluation:

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
 output_eval_dataset.jsonl
             |
             v
             S3
             |
             v
  Bedrock Evaluations
             |
             v
      Amazon Nova Pro
       LLM-as-a-Judge
             |
             v
       Final Scores
```

---

# 25. Conclusion

This project demonstrates an end-to-end agentic customer-support workflow using AWS services.

The final system combines:

- Amazon Bedrock Flows for classification and routing
- Amazon Bedrock AgentCore for the bug-report agent workflow
- AgentCore Gateway for tool integration
- AWS Lambda for backend tool execution
- Amazon DynamoDB for persistent bug reports
- Automated testing using the AgentCore harness
- Amazon S3 for evaluation datasets and results
- Amazon Bedrock Evaluations for automated quality assessment
- Amazon Nova Pro as the LLM-as-a-Judge evaluator

The final submission should include the implementation, automated tests, evaluation dataset, evaluation results, architecture documentation, and the screenshots required by the project rubric.
