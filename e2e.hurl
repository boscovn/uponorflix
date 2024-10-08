PUT {{API_URL}}/movies
{
  "title": "The Shawshank Redemption",
  "year": 1994,
  "genre": "Drama"
}
HTTP 200
[Captures]
shawshank_id: jsonpath "$.id"
[Asserts]
jsonpath "$.title" == "The Shawshank Redemption"
jsonpath "$.year" == 1994
jsonpath "$.genre" == "Drama"

GET {{API_URL}}/movies
HTTP 200
[Asserts]
jsonpath "$.movies[0].title" == "The Shawshank Redemption"
jsonpath "$.movies[0].year" == 1994
jsonpath "$.movies[0].genre" == "Drama"

DELETE {{API_URL}}/movies/{{shawshank_id}}
HTTP 204

GET {{API_URL}}/movies
HTTP 200
[Asserts]
jsonpath "$.movies" count == 0

# PUT 3 different movies with differing years, 2 with the same genre
PUT {{API_URL}}/movies
{
  "title": "The Shawshank Redemption",
  "year": 1994,
  "genre": "Drama"
}
HTTP 200
[Captures]
shawshank_id: jsonpath "$.id"

PUT {{API_URL}}/movies
{
  "title": "The Godfather",
  "year": 1970,
  "genre": "Drama"
}
HTTP 200
[Captures]
godfather_id: jsonpath "$.id"

PUT {{API_URL}}/movies
{
  "title": "The Dark Knight",
  "year": 2008,
  "genre": "Action"
}
HTTP 200
[Captures]
dark_knight_id: jsonpath "$.id"


GET {{API_URL}}/movies
HTTP 200
[Asserts]
jsonpath "$.movies" count == 3

GET {{API_URL}}/movies
[QueryStringParams]
genre: Drama
HTTP 200
[Asserts]
jsonpath "$.movies" count == 2

GET {{API_URL}}/movies
[QueryStringParams]
genre: Action
HTTP 200
[Asserts]
jsonpath "$.movies" count == 1

GET {{API_URL}}/movies
[QueryStringParams]
year_start: 1990
HTTP 200
[Asserts]
jsonpath "$.movies" count == 2


GET {{API_URL}}/movies
[QueryStringParams]
year_start: 1990
year_end: 2000
HTTP 200
[Asserts]
jsonpath "$.movies" count == 1


PUT {{API_URL}}/movies
{
  "title": "The Godfather",
  "year": 1970,
  "genre": "Drama",
  "id": "{{godfather_id}}"
}
HTTP 200


GET {{API_URL}}/movies
HTTP 200
[Asserts]
jsonpath "$.movies" count == 3


DELETE {{API_URL}}/movies/{{shawshank_id}}
HTTP 204

DELETE {{API_URL}}/movies/{{godfather_id}}
HTTP 204

DELETE {{API_URL}}/movies/{{dark_knight_id}}
HTTP 204
