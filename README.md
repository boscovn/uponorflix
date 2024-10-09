# Uponorflix

This project addresses the task defined [here](task.md).

It consists of a set of aws lambda functions, each with its own directory in the functions/
directory.

The functions are:
- `get-movies`: returns a list of movies
- `add-or-update-movie`: adds a new movie or updates an existing one
- `delete-movie`: deletes a movie

The functions are deployed using a SAM template in the template.yaml file, which is a superset of
CloudFormation.
The template also defines a DynamoDB table to store the movies.

## Get movies
The `get-movies` function returns a list of movies.
It is invoked with a GET request to the /movies endpoint.
It accepts the following query parameters:
- `genre`: filters the movies by genre
- `year_start`: filters the movies by the year they were released, defaults to 0
- `year_end`: filters the movies by the year they were released, defaults to 3000
- `limit`: limits the number of movies returned, defaults to 10. It must be a positive integer less than 100.
- `start_key`: used to paginate the results, it is returned in the response and should be passed in the next request.

## Add or update movie
The `add-or-update-movie` function adds a new movie or updates an existing one.
It is invoked with a PUT request to the /movies endpoint.
The body of the request must be a JSON object with the following fields:
- `title`: the title of the movie
- `genre`: the genre of the movie
- `year`: the year the movie was released
- `id`: the id of the movie, if it is not provided a new id is generated

## Delete movie
The `delete-movie` function deletes a movie.
It is invoked with a DELETE request to the /movies/{id} endpoint.
The id of the movie to delete must be passed in the URL.


## Deployment

To deploy the stack, it is a requirement to have the AWS CLI installed and configured with
the necessary permissions and to have the sam cli installed.
```bash
sam deploy --guided
```

## Testing

### Unit testing
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
Then in another terminal run the tests.
You need to have [hurl](https://hurl.dev/) installed.
Run the following command:
```bash
hurl --test e2e.hurl --variable API_URL=http://localhost:3000
```
Note that you can change the API_URL variable to test against a different environment, but the tests will fail if there are already movies in the database.

### CI/CD
Note that both the unit and end-to-end tests are run in workflows in GitHub Actions.
You can see the results in the Actions tab of this repository.
As of now there is no deployment workflow, but it could be easily added with the `sam deploy` command.
