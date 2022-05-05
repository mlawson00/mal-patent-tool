import logo from './ServomexVisualAssets/Hummingbird Logo Group.png';
import logo2 from './ServomexVisualAssets/Logo512.png';
import './App.css';
import React from "react";

// const googleLogin = () => {
//     var auth_provider = "google-oidc"
//     var login_url = "http://127.0.0.1:8000/login-redirect"
//     //window.location.href = login_url
//     //props.funky()
//     console.log(login_url)
// }

const loginPage = (props) => {

    console.log(props)

    return (
        <div className="App_login">
            <header className="App-header">
                <div className="flex_container_horizontal">
                    <div className="flex_container_vertical">
                        <img src={logo2} className="App-logo-small" alt="logo" align="start"/>
                        <p className='Title-text'>
                            MAL-L7
                        </p>
                        {/*<img src={logo2} className="App-logo-small" alt="logo" align="start"/>*/}
                        <button onClick={props.googleLogin}>Login with Google</button>
                    </div>

                    <div className="flex_container_horizontal_orange"/>

                </div>

            </header>
        </div>
    );
}
export default loginPage;