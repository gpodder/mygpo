function(doc)
{
    if(doc.doc_type == 'User')
    {
        for(id in doc.devices)
        {
            device = doc.devices[id];

            device.user_oldid = doc.oldid;
            device.user = doc._id;

            emit([doc.oldid, device.uid], device);
        }
    }
}
