function(doc)
{
    if(doc.doc_type != "Episode")
    {
        return;
    }

    function searchObject(obj, languages, types)
    {
        if (obj.language)
        {
            languages.push(obj.language.slice(0, 2));
        }

        if (obj.content_types)
        {
            for(n in obj.content_types)
            {
                types.push(obj.content_types[n]);
            }
        }
    };

    function doEmit(date_str, types, languages, value)
    {
        if(value > 0)
        {
            emit([date_str, "none", value], null);

            for(n in types)
            {
                emit([date_str, "type", types[n], value], null);

                for(m in languages)
                {
                    emit([date_str, "type-language", types[n], languages[m], value], null);
                }
            }

            for(m in languages)
            {
                emit([date_str, "language", languages[m], value], null);
            }
        }
    };

    var toplist_period = 7;

    if(doc.listeners <= 0 || doc.released == null)
    {
        return;
    }

    dateString = doc.released.slice(0, 10);
    dateParts = dateString.split("-");
    dateParts = dateParts.map(Number);

    languages = [];
    types = [];

    searchObject(doc, languages, types);

    for(i=0; i<toplist_period; i++)
    {
        dateObj = new Date(dateParts[0], dateParts[1]-1, dateParts[2]+i);
        year = dateObj.getFullYear();
        month = Number(dateObj.getMonth()) + 1;
        if(month < 10)
        {
            month = "0" + month;
        }
        day = Number(dateObj.getDate());
        if(day < 10)
        {
            day = "0" + day;
        }

        dateStr = year + "-" + month + "-" + day;

        doEmit(dateStr, types, languages, doc.listeners);
    }
}
