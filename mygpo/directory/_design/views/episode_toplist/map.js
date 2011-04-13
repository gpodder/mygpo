function(doc)
{
    var toplist_period = 7;

    if(doc.doc_type == "Episode")
    {
        if(doc.listeners <= 0 || doc.released == null)
        {
            return;
        }

        dateString = doc.released.slice(0, 10);
        dateParts = dateString.split("-");
        dateParts = dateParts.map(Number)

        for(n=0; n<toplist_period; n++)
        {
            dateObj = new Date(dateParts[0], dateParts[1]-1, dateParts[2]+n);
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

            emit([dateStr, doc.listeners], null);
        }
    }
}
