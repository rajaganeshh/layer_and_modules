import React from 'react';
import {
  Box,
  Typography,
  Grid
} from '@mui/material';

// Data for change requests
// const changeRequests = [
//   {
//     id: 'CHG0063375',
//     shortDescription: 'iOS fix version 4.1.82',
//     type: 'Emergency',
//     state: 'Scheduled',
//     startDate: 'October 3, 2024, 10:00 AM',
//     endDate: 'October 7, 2024, 5:00 PM',
//     service: 'Digital Channels',
//     description: 'Fixes for iOS 16.1.1 users experiencing app issues preventing bookings, leading to revenue losses.',
//     justification: 'Users unable to make bookings hit revenue; fix applied through WebKit recommended code.',
//     status: 'Approved',
//     impact: '2 - Medium Risk'
//   },
//   {
//     id: 'CHG0063480',
//     shortDescription: 'eRes Reservation System - Update/Delete problematic booking-related data from transactional tables.',
//     type: 'Standard',
//     state: 'New',
//     startDate: 'October 4, 2024, 12:30 PM',
//     endDate: 'October 4, 2024, 1:30 PM',
//     service: 'Passenger Reservations',
//     description: '',
//     justification: '',
//     status: '',
//     impact: ''
//   },
//   {
//     id: 'CHG0063510',
//     shortDescription: 'Backend cleanup job for stale session tokens',
//     type: 'Standard',
//     state: 'In Progress',
//     startDate: 'October 5, 2024, 2:00 PM',
//     endDate: 'October 5, 2024, 3:00 PM',
//     service: 'Authentication Service',
//     description: 'Scheduled cleanup to improve login performance and reduce stale sessions.',
//     justification: 'Frequent stale tokens caused multiple login issues.',
//     status: 'Approved',
//     impact: '1 - Low Risk'
//   }
// ];

// // Data for similar change requests
// const similarRequests = [
//   {
//     id: 'CHG0063400',
//     shortDescription: 'Android fix version 5.2.10',
//     type: 'Emergency',
//     state: 'Scheduled',
//     startDate: 'October 8, 2024, 10:00 AM',
//     endDate: 'October 10, 2024, 5:00 PM',
//     service: 'Digital Channels',
//     description: 'Fixes for Android users experiencing app crashes during payment.',
//     justification: 'Critical issue affecting payment flows.',
//     status: 'Approved',
//     impact: '2 - Medium Risk'
//   }
// ];

// // Data for knowledge base articles
// const knowledgeBase = [
//   {
//     id: 1,
  
//     content: 'Akamai GTM: Global Traffic Management (GTM) Service from Akamai is used as a load balancer (using DNS) for balancing the traffic in vaa data centers (Dickland and Reading). Refer to the Akamai GTM Confluence page for more information. (Source: vaa Akamai CDN WAF and External DNS.docx]'
//   },
//   {
//     id: 2,
 
//     content: 'vaa has a single WAF configuration file used for all vaa websites, which is version controlled. Refer to section 7.1.6 in the SOP Akamai Ruebook for more details. [Source: vaa_Akamai CON WAF aed Extornal DNS.docx]'
//   },
//   {
//     id: 3,
 
//     content: 'To check for Akamai control center outages, refer to the status page at https://www.akamaistatus.com/ and contect vendor support to raise a case if necessary. [Source: vaa Akamai CDN WAF and External DNS.docx]'
//   },
//   {
//     id: 4,
 
//     content: 'Alkarnai caches web content to respond to user requests from Edge Servers. In cases of stale content, Akamai reachas the Origin Servers (hosted on vaa AWS Cloud or on-premises DCs). [Source: vaa_Akamai CDN WAF and External DNS.docx]'
//   },
//   {
//     id: 5,
 
//     content: 'Akamai WAF: The Web Application Firewall provides scalable protection against web application attacks like SQL injections and XSS, while triaintaining, application performance. It operates on a layer 7 firewall in partnership with SiteShield. [Source: easyuint_Akamai CON WAF and Exspmal DNS docx]'
//   },
// ];

// const renderContentWithLinks = (content) => {
//     // Regular expression to match URLs
//     const urlRegex = /(https?:\/\/[^\s]+)/g;
  
//     // Split the content into parts based on URLs
//     const parts = content.split(urlRegex);
  
//     return parts.map((part, index) => {
//       // If the part matches the URL regex, render it as a clickable link
//       if (urlRegex.test(part)) {
//         return (
//           <a
//             key={index}
//             href={part}
//             target="_blank"
//             rel="noopener noreferrer"
//             style={{ color: 'blue', textDecoration: 'underline' }}
//           >
//             {part}
//           </a>
//         );
//       }
//       // Otherwise, render it as plain text
//       return <span key={index}>{part}</span>;
//     });
//   };

  const handleTitle = (value) => {
    if(value === "Recent Changes"){
      return <text>Change Request</text>
    }
    if(value === "Recent Incidents"){
      return <text>Recent Incidents</text>
    }
    if(value === "Knowledge Articles"){
     return <text>Knowledge articles</text>
    }
  }

const ChangeRequests = ({ value,data }) => {
  return (
    <Box sx={{ fontSize: "16px" }}>
      <Grid container spacing={2}>
        {/* Render for "Recent" */}
        
          {data.map((cr, index) => (
            <Grid item xs={12} key={cr.id}>
              <Box sx={{ p: 1 }}>
                <Typography sx={{ mb: 1 }}>
                  <strong>{index + 1}. {handleTitle(value)}: {cr.id}</strong>
                </Typography>
                <ul style={{ margin: 0, paddingLeft: '2rem' }}>
                  <li><strong   sx={{
                  whiteSpace: "pre-line", // Interpret \n as line breaks
                wordBreak: "break-word",
                
              }}>Summary:</strong> {cr.summary}</li>
                  <li><strong >Time:</strong> {cr.time}</li>
                  {/* <li><strong>State:</strong> {cr.state}</li> */}
                  {/* <li><strong>Planned Start Date:</strong> {cr.startDate}</li>
                  <li><strong>Planned End Date:</strong> {cr.endDate}</li>
                  <li><strong>Business Service Affected:</strong> {cr.service}</li>
                  {cr.description && <li><strong>Description:</strong> {cr.description}</li>}
                  {cr.justification && <li><strong>Justification:</strong> {cr.justification}</li>}
                  {cr.status && <li><strong>Approval Status:</strong> {cr.status}</li>}
                  {cr.impact && <li><strong>Impact:</strong> {cr.impact}</li>} */}
                </ul>
              </Box>
            </Grid>
          ))
        }

        {/* Render for "Similar" */}
        {/* {value === "Similar" &&
          similarRequests.map((sr, index) => (
            <Grid item xs={12} key={sr.id}>
              <Box sx={{ p: 1 }}>
                <Typography sx={{ mb: 1 }}>
                  <strong>{index + 1}. Similar Request: {sr.id}</strong>
                </Typography>
                <ul style={{ margin: 0, paddingLeft: '2rem' }}>
                  <li><strong>Short Description:</strong> {sr.shortDescription}</li>
                  <li><strong>Type:</strong> {sr.type}</li>
                  <li><strong>State:</strong> {sr.state}</li>
                  <li><strong>Planned Start Date:</strong> {sr.startDate}</li>
                  <li><strong>Planned End Date:</strong> {sr.endDate}</li>
                  <li><strong>Business Service Affected:</strong> {sr.service}</li>
                  {sr.description && <li><strong>Description:</strong> {sr.description}</li>}
                  {sr.justification && <li><strong>Justification:</strong> {sr.justification}</li>}
                  {sr.status && <li><strong>Approval Status:</strong> {sr.status}</li>}
                  {sr.impact && <li><strong>Impact:</strong> {sr.impact}</li>}
                </ul>
              </Box>
            </Grid>
          ))
        } */}

        {/* Render for "Knowledge" */}
        {/* {value === "Knowledge" &&
          knowledgeBase.map((kb, index) => (
            <Grid item xs={12} key={kb.id}>
              <Box sx={{ p: 1,fontSize:"14px" }}>
               
     <Typography>
                    <ul>
                    <li>{renderContentWithLinks(kb.content)}</li>
                    </ul>
                    </Typography>
           
              </Box>
            </Grid>
          ))
        } */}
      </Grid>
    </Box>
  );
};

export default ChangeRequests;
