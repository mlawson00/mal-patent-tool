import React, {Component, useState} from 'react';


class App extends Component {

    state = {
        producerLoginRedirectEndpoint: 'api/login-redirect',
        producerLoginEndpoint: 'api/login/',
        producerLogoutEndpoint: 'api/logout/',
        producerLoginCheckEndpoint: 'api/user-session-status/',
        userLoggedIn: false,
        userName: null,
    }

    componentDidMount() {
        // this.authenticate()
    }

    setCookie = (cname, cvalue, exdays) => {
        var d = new Date();
        d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
        var expires = "expires=" + d.toUTCString();
        document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    }

    getCookie = (cname) => {
        var name = cname + "=";
        var decodedCookie = decodeURIComponent(document.cookie);
        var ca = decodedCookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) === 0) {
                return c.substring(name.length, c.length);
            }
        }
        return "";
    }

    authenticate = () => {
        var authToken = (window.location.search.match(/authToken=([^&]+)/) || [])[1]
        window.history.pushState('object', document.title, "/");

        if (authToken) {
            // Try to get an access token from the server
            this.getAccessToken(authToken)
        } else {
            // Check user is logged in
            this.checkUserSessionStatus()
        }
    }

    getAccessToken = (authToken) => {
        const request = {
            method: 'GET',
            headers: {
                "Authorization": "Bearer " + authToken
            },
            credentials: 'include'
        }

        fetch(this.state.producerLoginEndpoint, request)
            .then(response => {
                // Check user is logged in
                this.checkUserSessionStatus()
            })
            .then(data => {
            })
            .catch(err => {
            })
    }

    checkUserSessionStatus = () => {
        const request = {
            method: 'GET',
            credentials: 'include'
        }

        fetch(this.state.producerLoginCheckEndpoint, request)
            .then(response => response.json())
            .then(data => {
                this.setState({
                    userLoggedIn: data['userLoggedIn'],
                    userName: data['userName'],
                })
            })
            .catch(err => {
            })
    }

    logout = () => {
        const request = {
            method: 'GET',
            credentials: 'include'
        }

        fetch(this.state.producerLogoutEndpoint, request)
            .then(response => response.json())
            .then(data => {
                window.location.reload()
            })
            .catch(err => {
            })
    }

    getPatentData = () => {

        const [searchTerm, setSearchTerm] = useState('')
        const [tokens, setTokens] = useState([])
        const [searchedTerm, setSearchedTerm] = useState('')
        const [processedQuery, setProcessedQuery] = useState('')
        const [loading, setLoading] = useState(false)


        const handleChange = (event) => {
            setSearchTerm(event.target.value)
        };

        const getAPI = () => {

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'abstract': searchTerm})
            }

            const processResponse = (response) => {

                setTokens(response.inputs.text)
                console.log(response.inputs.text)
                setLoading(true)

                const requestOptions = {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        'input_mask': response.inputs.input_mask,
                        'input_type_ids': response.inputs.input_type_ids,
                        'input_word_ids': response.inputs.input_word_ids
                    })
                }

                fetch('get_BERT_probs', requestOptions)
                    .then((response) => response.json())
                    .then((response)=> console.log(response))

            }

            fetch('abstract_search', requestOptions).then((response) => response.json()).then((response => processResponse(response)))
                .then(setSearchedTerm(searchTerm))
        }

        const yikes = tokens.map(name => <strong>{name} </strong>)


        return (
            <div>
                <button onClick={getAPI}>Get Data</button>
                <input id="search" type="text" onChange={handleChange}/>
                {searchedTerm !== "" ?
                    <><p>Searching for: <strong>{searchedTerm}</strong></p>
                        <p>Tokens: {yikes}</p></>
                    : null}
            </div>
        )
    }

    render() {
        return (
            <section id="page-container">
                {this.state.userLoggedIn ?
                    <div>
                        <div>
                            You are now logged in!
                        </div>
                        <this.getPatentData></this.getPatentData>
                        <div>
                            <button onClick={this.logout}>Logout</button>
                        </div>
                    </div> :
                    //  this is the pair of login boxes, maybe could be fleshed out more!
                    <Login producerLoginRedirectEndpoint={this.state.producerLoginRedirectEndpoint}/>
                }
            </section>
        );
    }
}


function Login(props) {
    const googleLogin = () => {
        var auth_provider = "google-oidc"
        var login_url = props.producerLoginRedirectEndpoint + "?auth_provider=" + auth_provider
        window.location.href = login_url
    }

    return (
        <section>
            <div>
                <button onClick={googleLogin}>Login with Google</button>
            </div>
        </section>
    );
}

export default App;