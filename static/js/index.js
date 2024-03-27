function redirectToStudent() {
    fetch('/student.html')
        .then(response => {
            if (response.ok) {
                console.log('Student page fetched successfully');
                window.location.href = "/student.html";
            } else {
                console.error('Error:', response.statusText);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
function redirectToAdmin() {
    fetch('/admin.html')
        .then(response => {
            if (response.ok) {
                console.log('student page fetched successfully');
                window.location.href = "/admin.html";
            } else {
                console.error('Error:', response.statusText);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}


