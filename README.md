# RTP_Media_Server
Computer Networks 2021 Fall term project

## How to execute?
install required libraries
```
python -m pip install -r requirements.txt
```

run server
```
python test_server.py -a <server ip>
# e.g. python test_server.py -a 127.0.0.1
```

run client (in another terminal)
```
python main_client.py -a <server ip> -n <file>
# e.g. python main_client.py -a 127.0.0.1 -n movie5.mp4
```