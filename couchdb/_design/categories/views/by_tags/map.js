function(doc)
{
    if (doc.doc_type == "Category")
    {
        emit(doc.label, null);
        for(i in doc.spellings)
        {
            emit(doc.spellings[i], null);
        }
    }

}
