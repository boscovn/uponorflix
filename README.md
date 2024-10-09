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

Instead of mocking the DynamoDB database, I instantiate one with the [test containers](https://testcontainers.org/) library.
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
As of now there is no deployment workflow, but it could be easily added with the `sam deploy` command, and the necessary secrets.


## Additional considerations

### Security
Due to time constraints, I didn't implement any security measures. The endpoints need to be protected, at the very least those that modify the database. (add-or-update-movie and delete-movie).
A more granular approach would be to protect all the endponts with different roles.
I have experienced setting up cognito with API Gateway and Lambda in the AWS console after deploying the stack to my personal account, but I could't manage to make it work with SAM.

### Error handling
I have added some error handling in the functions, but it could be improved.
I have also added some tests to check that the functions return the correct status code and error message.

### Logging
I mainly log errors exclusively. More verbose logging could be added to help with debugging as well as cloudwatch logs with the appropriate alerts.

### Movie posters
As of now there are no movie posters, but they could be added to the database as a URL to an S3 bucket. The method for uploading the images could be a separate lambda function that receives the image and returns the URL.
That or modify the add-or-update-movie function to accept a base64 encoded image and upload it to S3.

### More movie details
As of now only a limited set of details are stored for each movie. More details could be added, like the director, the cast, the plot, etc, and also the possibility to add multiple genres.
With more details, the get-movies function could accept more query parameters to filter the movies, or even a search parameter for full-text search.

### More endpoints
More endpoints could be added. As of now, the only way to get a movie is by queries for the catalog. An endpoint to get a movie by id could be added.
The add or update movie endpoint could be split into two separate endpoints, one for adding and one for updating with different http methods, POST and PUT respectively.
I went with the single endpoint approach to keep it simple and because it seemed that the task was asking for it.

### Table Schema
As of now, the ohly index in the table is the id. A more complex schema could be worth considering, different indexes if queying  by them is common.

### GitOps
The current workflow triggers the unit test matrix and the end-to-end tests on every push to the master branch and not on pull requests.
Since this assignment is something only I work in and that for the sake of simplicity I have it in a public repository, workflows are only triggered by pushes to the master branch and not on pull requests.
A more complex workflow could be implemented that triggers the tests on pull requests as well and the branching strategy could follow the environment strategy, with a development branch and a production branch, maybe even a staging branch.
Pushes to those branches would be restricted and only allowed through pull requests. Ideally only sending pull requests to the development branch and then merging to the staging branch and then to the production branch. With a defined process for approving pull requests.
