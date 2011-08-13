function (keys, values, rereduce)
{
    function unique(arr) {
        var a = [];
        var l = arr.length;
        for(var i=0; i<l; i++) {
            for(var j=i+1; j<l; j++) {
                if (arr[i] === arr[j])
                    j = ++i;
            }
            a.push(arr[i]);
        }
        return a;
    };

    if (rereduce)
    {
        return sum(values)
    }
    {
        /* We count one per user, not per play-event */
        val = unique(values);
        return val.length;
    }
}
