DELETE FROM `sanitizing_rules`;
INSERT INTO `sanitizing_rules` VALUES (1,1,1,'feeds2\\.feedburner\\.com','feeds.feedburner.com',1,'Rewriting for feedburner should happen as \"feeds2.feedburner.com\" -> \"feeds.feedburner.com\"');
INSERT INTO `sanitizing_rules` VALUES (2,1,1,'(?P<unchanged>feedburner\\.com.+)\\?format=xml','\\g<unchanged>',2,'Feedburner URLs should have their \"?format=xml\" query string removed: \r\n\r\nhttp://feeds2.feedburner.com/linuxoutlaws?format=xml \r\nhttp://feeds.feedburner.com/linuxoutlaws \r\n');
INSERT INTO `sanitizing_rules` VALUES (3,1,1,'^\\s+','',0,'Remove leading whitespaces');
INSERT INTO `sanitizing_rules` VALUES (4,1,1,'\\s+$','',0,'Remove trailing whitespaces');
INSERT INTO `sanitizing_rules` VALUES (5,1,1,'^[^(https?):].+','',100,'Empty any string that doesn\'t start with either http or https');
INSERT INTO `sanitizing_rules` VALUES (6,1,1,'^https?://([0-9a-zA-z-\.]+\.)?gpodder.org.*','',100,'As gpodder.org doesn\'t host Podcasts, all URLs starting with this domain are considered invalid');
INSERT INTO `sanitizing_rules` VALUES (7,1,0,'(?P<unchanged>feedburner\\.com.+)\\/$','\\g<unchanged>',2,'Feedburner URLs sometimes have a trailing slash, which can be removed safely');
INSERT INTO `sanitizing_rules` VALUES (8,1,1,'^.*[^\\x20-\\x7E].*$', '', 50, 'Remove URLs with non-ascii characters');
INSERT INTO `sanitizing_rules` VALUES (9,1,0,'^http://leoville\\.tv/podcasts/(?P<podcast>\\w+)\\.xml$', 'http://leo.am/podcasts/\\g<podcast>', 10, 'Rewrite URLs of TWiT Podcasts because most users use a URL that is going to break soon (bug 885)');
INSERT INTO `sanitizing_rules` VALUES (10,1,0,'^http://www\\.dancarlin\\.com/dchh\\.xml$', 'http://feeds.feedburner.com/dancarlin/history', 10, 'Rewrite podcast URL of Dan Carlin\'s Hardcore History because the old URL doesn\'t work anymore (bug 855)');

