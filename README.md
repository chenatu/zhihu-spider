知乎爬虫
----

在python3上利用urllib与BeautifulSoup开发的最简单的知乎（www.zhihu.com）爬虫

`getTopics()`可以获得所有的以及topic信息

`getSubTopics`和`getSubTopic`或者一级话题下面的所有子话题以及第一子话题。第一子话题是与该话题一致的大类话题

`getTopicBestPeople()`获得自话题下的最佳回答者

`getPersonInfo()`获取回答者基本信息

`getAnswerByDefaultOrder()`用来获取某人按照点赞数排序的某条答案

`getAnswerContent()`用来获取某条答案的详细内容

需要注意的是，知乎貌似会屏蔽连续对知乎的访问，所以需要请求之间有一个等待延时。

同时，知乎的某些网页以及网页的某些组件对未登录用户是不公开的，所以需要进行登陆，将cookies获取到之后放入程序的全局`headers`变量中

最后，urllib并不是一个很好的爬虫，再运行一段时间后有可能会出现程序假死，要么增加try catch进行重试，要么可以采用更高效的scrapy框架