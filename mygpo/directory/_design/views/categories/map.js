function (doc)
{
    if (doc.doc_type == "Category")
    {
        emit(doc.weight, doc);
    }
}

