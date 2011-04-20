function (doc)
{
    if (doc.doc_type == "Category")
    {
        weight = 0;
        for(n in doc.podcasts)
        {
            weight += doc.podcasts[n].weight;
        }

        emit(weight, doc.label);
    }
}

