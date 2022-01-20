# RTP_Media_Server
computer networks term project

## 分工
server 江  
client 林  
GUI & read 翁

## 現成 code
### 課本習題 
https://media.pearsoncmg.com/aw/aw_kurose_network_3/labs/lab7/lab7.html  
https://github.com/gabrieljablonski/rtsp-rtp-stream


### other implementations
https://github.com/mutaphore/RTSP-Client-Server  
https://github.com/aler9/rtsp-simple-server  
https://github.com/gabrieljablonski/rtsp-rtp-stream/aw/aw_kurose_network_3/labs/lab7/lab7.html

## read mp4
opencv
https://learnopencv.com/read-write-and-display-a-video-using-opencv-cpp-python/  
https://blog.csdn.net/liuweizj12/article/details/80235065

FFmpeg stream video to rtmp from frames OpenCV python
https://pretagteam.com/question/ffmpeg-stream-video-to-rtmp-from-frames-opencv-python

## RTP packet
![](https://www.researchgate.net/profile/Jill-Slay/publication/221352750/figure/fig2/AS:337330847141894@1457437349689/presents-the-RTP-packet-header-format-In-RTP-the-Synchronization-Source-SSRC-field.png)

CSRC not needed 
> SSRC Identifies the synchronization source. The value is chosen randomly, with the intent that no two synchronization sources within the same RTP session will have the same SSRC. Although the probability of multiple sources choosing the same identifier is low, all RTP implementations must be prepared to detect and resolve collisions. If a source changes its source transport address, it must also choose a new SSRC to avoid being interpreted as a looped source.

> CSRC An array of 0 to 15 CSRC elements identifying the contributing sources for the payload contained in this packet. The number of identifiers is given by the CC field. If there are more than 15 contributing sources, only 15 may be identified. CSRC identifiers are inserted by mixers, using the SSRC identifiers of contributing sources. For example, for audio packets the SSRC identifiers of all sources that were mixed together to create a packet are listed, allowing correct talker indication at the receiver.

> To be honest, I have never seen anyone actually use SSRC or CSRC in any meaningful way. In all the code I've dealt with, we just generate a random number in SSRC and don't never bother filling in CSRC. 

https://stackoverflow.com/a/21951323/15493213

## video convertion
<http://zulko.github.io/blog/2013/09/27/read-and-write-video-frames-in-python-using-ffmpeg/>  
`ffmpeg -i my-input.mp4 my-output.mjpeg`
