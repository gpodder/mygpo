function(doc)
{
    if(doc.doc_type != "Episode")
    {
        return;
    }

    function getLanguage(podcast)
    {
        if (podcast.language)
        {
            return podcast.language.slice(0, 2);
        }

        return null;
    };

    function doEmit(date_str, language, listeners)
    {
        if(listeners <= 0)
        {
            return;
        }

        emit([date_str, "", listeners], null);

        if(language)
        {
            emit([date_str, language, listeners], null);
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

    var language = getLanguage(doc);

    for(var i=0; i<toplist_period; i++)
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

        doEmit(dateStr, language, doc.listeners);
    }
}
