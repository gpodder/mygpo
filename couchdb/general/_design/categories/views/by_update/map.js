function (doc)
{
    if (doc.doc_type == "Category")
    {
        if(doc.updated && (doc.podcasts.length > 10))
        {
            emit(doc.updated, [doc.label, doc.podcasts.length]);
        }
    }
}

