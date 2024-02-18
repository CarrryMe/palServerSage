name=SageServer
pid=$(ps -ef | grep $name | grep -v grep | awk '{print $2}')
if [ "$pid"x = "x" ]; then
echo $name  is stop
else
echo $name pid is $pid
kill -9 $pid
echo kill is ok
fi

