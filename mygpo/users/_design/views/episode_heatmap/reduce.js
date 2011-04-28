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
        flattened = []
        for(n in arr)
        {
            for(x in arr[n])
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

    if (rereduce)
    {
        all_borders = [];
        for(n in values)
        {
            all_borders.push(values[n].borders);
        }
    }
    else
    {
        all_borders = values;
    }

    borders = flatten(all_borders);
    borders = unique(borders);
    borders.sort(sortNumerical);

    heatmap = [];

    for(n=0; n<borders.length-1; n++)
    {
        heatmap.push(0);
    }

    for(n in values)
    {
        j = 0;

        if(rereduce)
        {
            length = values[n].borders.length-1;
            increment = 1;
            function heat_val(i) { return values[n].heatmap[i]; };
        }
        else
        {
            length = values[n].length;
            increment = 2;
            heat_val = 1;
            function heat_val(i) { return 1; };
        }


        for(i=0; i<length; i+=increment)
        {
            from  = values[n][i];
            until = values[n][i+1];

            while(borders[j] < from)
            {
                j++;
            }

            while(borders[j] < until)
            {
                heatmap[j++] += heat_val(i);
            }
        }
    }

    return {heatmap: heatmap, borders: borders};
}
