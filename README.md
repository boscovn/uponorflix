# Uponorflix

This project addresses the task defined [here](task.md).

I consists of a set of aws lambda functions, each with its own directory in the functions/
directory.

The functions are:
- `get-movies`: returns a list of movies
- `add-or-update-movie`: adds a new movie or updates an existing one
- `delete-movie`: deletes a movie

The functions are deployed using a SAM template in the template.yaml file, which is a superset of
CloudFormation.
The template also defines a DynamoDB table to store the movies.

## Deployment

To deploy the stack, it is a requirement to have the AWS CLI installed and configured with
the necessary permissions and to have the sam cli installed.
```bash
sam deploy --guided
```

## Testing
Each function has its own tests.
To test a function go to its directory, install the dependencies and run the tests.
```bash
cd functions/get-movies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```
Do the same for the other functions, 
remember to deactivate the virtual environment before activating a new one.

Instead of mocking the DynamoDB database, I use a real one with the [test containers](https://testcontainers.org/) library.
So having Docker installed is a requirement to run the tests.

### End-to-end testing
To test the whole stack, run the following command:
```bash
docker-compose up -d
sam build && sam local start-api --docker-network uponorflix_uponorapi
```
Then in another terminal run the tests:
```bash
hurl --test e2e.hurl --variable API_URL=http://localhost:3000
```






