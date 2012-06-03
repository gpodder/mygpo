function(newDoc, oldDoc, userCtx)
{

    if(newDoc.doc_type == "User")
    {
        var device_uids = [];
        var device_ids = [];

        for(var n in newDoc.devices)
        {
            var device = newDoc.devices[n];

            if(device_ids.indexOf(device.id) > -1)
            {
                throw({forbidden: "Duplicate Device-Id " + device.id +
                        " for user " + newDoc._id});
            }

            device_ids.push(device.id);

            if(device_uids.indexOf(device.uid) > -1)
            {
                throw({forbidden: "Duplicate Device-UID " + device.uid +
                        " for user " + newDoc._id});
            }

            if(!device.uid.match("^[\\w_.-]+$"))
            {
                throw({forbidden: "Invalid Device-UID " + device.uid +
                        " for user " + newDoc._id});
            }

            device_uids.push(device.uid);
        }

        for(var n in newDoc.sync_groups)
        {
            var group = newDoc.sync_groups[n];

            if(group.length < 2)
            {
                throw({forbidden: "Sync-Group " + n + " must contain at " +
                        "least two devices for user " + newDoc._id});
            }

            for(var i in group)
            {
                var device_id = group[i];

                if(device_ids.indexOf(device_id) < 0)
                {
                    throw({forbidden: "Invalid Device-Id " + device_id +
                            " in Sync-Group " + n + " for user " +
                            newDoc._id});
                }
            }
        }
    }
}
