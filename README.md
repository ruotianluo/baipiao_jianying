# baipiao_jianying

起因是看到app store有人卖4.99刀。。。尼玛有4.99刀干嘛要白嫖。

另外今天试了pr的字幕识别。。。。。。太尼玛拉垮了。。。。。。（我有从adobe的同学那白票的adobe全家桶，付钱是不可能付钱的）

讲道理剪映的语音识别真的很准，中英夹杂都行。牛逼。

## Disclaimer

此代码仅供学习参考使用。

## 使用

把要识别的视频导入剪映（音频暂时不行。）识别字幕。

然后找到`/Users/{username}/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`

默认的话项目名字是当前时间。

然后进入到点进去就可以找到`draft_info.json`.

运行
```
python extract.py xxxxx/draft_info.json
```
然后就会生成一个文件在`draft_info.json`（和一个fcpxml文件，没测试过）在`Downloads`里面

然后我们需要把这个json文件转换成fcpxml.
当前我的方法是使用大排档剪辑助手，在导入的同时可以同时编辑。
