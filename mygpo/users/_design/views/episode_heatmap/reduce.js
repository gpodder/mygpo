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

    function flatten(arr)
    {
        var flattened = []
        for(var n in arr)
        {
            for(var x in arr[n])
            {
                flattened.push(arr[n][x]);
            }
        }
        return flattened
    };

    function sortNumerical(a, b)
    {
        if(a < b)
        {
            return -1;
        }
        else if (a > b)
        {
            return 1;
        }
        else
        {
            return 0;
        }
    };

    function mergeBorders(borders, maxBorders)
    {
        last = null;
        newBorders = [];

        lastBorder = borders[borders.length-1];
        minDist = lastBorder / maxBorders;

        for(var n in borders)
        {
            border = borders[n];

            if(last == null)
            {
            }
            else if (border == lastBorder)
            {
            }
            else if ((border - last) < minDist)
            {
                continue;
            }

            newBorders.push(border);
            last = border;
        }

        return newBorders;
    };

    var all_borders = [];

    if (rereduce)
    {
        for(var n in values)
        {
            all_borders.push(values[n].borders);
        }
    }
    else
    {
        all_borders = values;
    }

    var borders = flatten(all_borders);
    borders = unique(borders);
    borders.sort(sortNumerical);
    borders = mergeBorders(borders, 50);

    var heatmap = [];

    for(var n=0; n<borders.length-1; n++)
    {
        heatmap.push(0);
    }

    for(var n in values)
    {
        j = 0;
        var length = 0;
        var increment = 1;

        if(rereduce)
        {
            length = values[n].borders.length-1;
            increment = 1;
        }
        else
        {
            length = values[n].length;
            increment = 2;
        }


        for(var i=0; i<length; i+=increment)
        {
            var from = 0;
            var until = 0;

            if(rereduce)
            {
                from  = values[n].borders[i];
                until = values[n].borders[i+1];
            }
            else
            {
                from  = values[n][i];
                until = values[n][i+1];
            }

            while(borders[j] < from)
            {
                j++;
            }

            while(borders[j] < until)
            {
                if(rereduce)
                {
                    heatmap[j++] += values[n].heatmap[i];
                }
                else
                {
                    heatmap[j++] += 1;
                }
            }
        }
    }

    return {heatmap: heatmap, borders: borders};
}
