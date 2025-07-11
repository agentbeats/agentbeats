# Battle Royale Docker Container

## Build the container

```
docker build -t battle-royale-test .
```

## Run the container

```
docker run -d -p 2222:22 -p 8080:80 --name battle-royale-test battle-royale-test
```

## SSH into the container

- Users: red1/red1pass, red2/red2pass, red3/red3pass
- Example:
  ```
  ssh red1@localhost -p 2222
  # password: red1pass
  ```

## Test the web server

- As a user (e.g., red1), run:
  ```
  pip install Flask
  AGENT_NAME=red1 python3 test_server.py
  ```
- Then, from the host:
  ```
  curl http://localhost:8080/
  # Should print 'red1'
  ```

## Stop and remove the container

```
docker stop battle-royale-test && docker rm battle-royale-test
``` 