function(doc)
{
    if(doc.doc_type == "PodcastList")
    {
        var rating = 0;
        for(var n in doc.ratings)
        {
            rating += doc.ratings[n].rating;
        }

        if (rating > 0)
        {
            emit(rating, null);
        }
    }
}
